"""Tracks consumption of each Google SKU's free monthly allowance.

Route generation walks its tiers in quality order and needs to know, before it
calls anything, whether a tier's free allowance still has room for this job.
Google's own figures come from the BigQuery billing export, which lags hours —
far too slow to gate a job starting now — so this keeps a live local estimate.

Being an estimate, it can drift. The budgets are configurable precisely so they
can be set below the true allowance, leaving headroom for that drift rather
than sailing into paid usage on a miscount.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import text

from app.config import settings
from app.models.api_usage import ApiSku
from app.utilities.datetime_utils import current_billing_month

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.config import Settings

# Route Optimization bills per shipment; the Routes API bills per request.
# Surfaced so a caller never has to guess what a bare count means.
SKU_UNITS: dict[str, str] = {
    ApiSku.FLEET_ROUTING.value: "shipments",
    ApiSku.SINGLE_VEHICLE_ROUTING.value: "shipments",
    ApiSku.ROUTES_COMPUTE.value: "requests",
}


def fleet_routing_units(num_locations: int, num_vehicles: int) -> int:
    """Shipments one Fleet Routing request will be billed for.

    Route Optimization bills per shipment, and ``_build_payload`` sends one
    shipment per delivery *plus* one forced pickup per vehicle to stop drivers
    sitting idle. Counting only the deliveries undercounts every run by the
    vehicle count — about 14% on a typical group.

    ``test_quota_service`` pins this against the real payload builder, so the
    two cannot drift apart silently.
    """
    return num_locations + num_vehicles


class QuotaExhaustedError(Exception):
    """Raised when a SKU has no free room left for the requested units."""


async def record_usage_out_of_band(sku: ApiSku, units: int) -> None:
    """Record usage from a call that had no session to hand.

    For ungated Google calls made deep in a request — route polylines, say —
    which spend a SKU's allowance without going through the cascade. Left
    unrecorded, the counter under-reports, and the cascade would offer a tier
    room it no longer has. Undercounting is the direction that costs money.

    Opens its own session and commits: Google billed the call regardless of
    what the surrounding transaction eventually does. Never raises, because
    losing count is a smaller problem than failing the work that prompted it.
    """
    if units <= 0:
        return

    from app import models as app_models

    session_maker = app_models.async_session_maker_instance
    if session_maker is None:
        return

    try:
        service = QuotaService(logging.getLogger(__name__), settings)
        async with session_maker() as session:
            await service.record(session, sku, units)
            await session.commit()
    except Exception:
        logging.getLogger(__name__).warning(
            "Could not record %d %s against %s; the counter will under-report",
            units,
            SKU_UNITS[sku.value],
            sku.value,
            exc_info=True,
        )


class QuotaService:
    """Reserves and records usage against each SKU's monthly allowance."""

    def __init__(self, logger: logging.Logger, settings: Settings) -> None:
        self.logger = logger
        self.settings = settings

    def budget_for(self, sku: ApiSku) -> int:
        """The configured free allowance for a SKU, in that SKU's own unit."""
        budgets = {
            ApiSku.FLEET_ROUTING: self.settings.quota_fleet_routing_shipments,
            ApiSku.SINGLE_VEHICLE_ROUTING: (
                self.settings.quota_single_vehicle_shipments
            ),
            ApiSku.ROUTES_COMPUTE: self.settings.quota_routes_compute_requests,
        }
        return budgets[sku]

    async def units_used(
        self, session: AsyncSession, sku: ApiSku, month: str | None = None
    ) -> int:
        """Units consumed for a SKU this billing month."""
        result = await session.execute(
            text(
                "SELECT units_used FROM api_usage "
                "WHERE sku = :sku AND billing_month = :month"
            ),
            {"sku": sku.value, "month": month or current_billing_month()},
        )
        row = result.first()
        return int(row[0]) if row else 0

    async def try_reserve(
        self,
        session: AsyncSession,
        sku: ApiSku,
        units: int,
        month: str | None = None,
    ) -> bool:
        """Claim ``units`` against a SKU's allowance, if they fit.

        Returns True when the claim succeeded. The check and the increment are
        one statement so two jobs starting together cannot both read the same
        count and each conclude there is room — the loser's UPDATE simply
        matches no row.

        Reserving up front rather than recording afterwards means a crash
        mid-call overcounts rather than undercounts. That direction is
        deliberate: overcounting costs us a slightly worse route, undercounting
        costs money.
        """
        if units <= 0:
            return True

        billing_month = month or current_billing_month()
        budget = self.budget_for(sku)

        # Ensure the row exists before the guarded UPDATE. Doing the whole
        # thing as one upsert would let the INSERT branch through unguarded,
        # since ON CONFLICT's WHERE only applies to the update path.
        await session.execute(
            text(
                "INSERT INTO api_usage "
                "  (api_usage_id, sku, billing_month, units_used, "
                "   created_at, updated_at) "
                "VALUES (gen_random_uuid(), :sku, :month, 0, now(), now()) "
                "ON CONFLICT (sku, billing_month) DO NOTHING"
            ),
            {"sku": sku.value, "month": billing_month},
        )

        result = await session.execute(
            text(
                "UPDATE api_usage "
                "SET units_used = units_used + :units, updated_at = now() "
                "WHERE sku = :sku AND billing_month = :month "
                "  AND units_used + :units <= :budget "
                "RETURNING units_used"
            ),
            {
                "sku": sku.value,
                "month": billing_month,
                "units": units,
                "budget": budget,
            },
        )
        row = result.first()

        if row is None:
            self.logger.info(
                "%s has no free room for %d %s this month (budget %d)",
                sku.value,
                units,
                SKU_UNITS[sku.value],
                budget,
            )
            return False

        self.logger.info(
            "Reserved %d %s against %s (%d/%d used this month)",
            units,
            SKU_UNITS[sku.value],
            sku.value,
            int(row[0]),
            budget,
        )
        return True

    async def record(
        self,
        session: AsyncSession,
        sku: ApiSku,
        units: int,
        month: str | None = None,
    ) -> None:
        """Add usage unconditionally, past the budget if need be.

        For calls we do not gate — route polylines are issued as part of saving
        a generation and are not worth failing over — where the counter still
        has to reflect that the allowance was spent.
        """
        if units <= 0:
            return

        billing_month = month or current_billing_month()
        await session.execute(
            text(
                "INSERT INTO api_usage "
                "  (api_usage_id, sku, billing_month, units_used, "
                "   created_at, updated_at) "
                "VALUES (gen_random_uuid(), :sku, :month, :units, now(), now()) "
                "ON CONFLICT (sku, billing_month) DO UPDATE "
                "SET units_used = api_usage.units_used + :units, "
                "    updated_at = now()"
            ),
            {"sku": sku.value, "month": billing_month, "units": units},
        )

    async def release(
        self,
        session: AsyncSession,
        sku: ApiSku,
        units: int,
        month: str | None = None,
    ) -> None:
        """Hand back units reserved for a call that never reached Google.

        Only for failures we know were never billed — a timeout waiting on a
        response may well have been charged, so those keep their reservation.
        Clamped at zero so a stray release cannot drive the counter negative
        and manufacture free quota.
        """
        if units <= 0:
            return

        billing_month = month or current_billing_month()
        await session.execute(
            text(
                "UPDATE api_usage "
                "SET units_used = GREATEST(units_used - :units, 0), "
                "    updated_at = now() "
                "WHERE sku = :sku AND billing_month = :month"
            ),
            {"sku": sku.value, "month": billing_month, "units": units},
        )

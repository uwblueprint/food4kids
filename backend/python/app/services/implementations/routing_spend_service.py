"""Keeps paid route generation inside the project's GCP budget.

The billing export lags by hours, so approved requests are also written to
``routing_charge`` and counted until the export has caught up with them.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from sqlalchemy import func, text
from sqlmodel import col, select

from app.models.routing_charge import RoutingCharge
from app.utilities.datetime_utils import now_local

if TYPE_CHECKING:
    import logging
    from datetime import datetime

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from app.services.implementations.billing_service import (
        BillingService,
        BillingSummary,
    )

# Usage can land in an export later than its own time, so charges this far
# before the last refresh still count: double-counting beats missing spend.
EXPORT_LAG = timedelta(days=1)

# Any fixed number; every instance must take the same one.
SPEND_LOCK_KEY = 310_310


def usd_conversion_rate(summary: BillingSummary) -> float | None:
    """USD to the billing currency, or None when it cannot be known."""
    if summary.usd_conversion_rate is not None:
        return summary.usd_conversion_rate
    # No export rows yet this month, so no rate to read; only USD is safe.
    return 1.0 if summary.budget_currency == "USD" else None


class RoutingSpendService:
    """Approves and records paid routing requests against the GCP budget."""

    def __init__(
        self,
        logger: logging.Logger,
        billing_service: BillingService,
        session_maker: async_sessionmaker[AsyncSession],
        monthly_credit_usd: float,
    ) -> None:
        self.logger = logger
        self.billing_service = billing_service
        self.session_maker = session_maker
        self.monthly_credit_usd = monthly_credit_usd

    async def try_charge(self, tier: str, shipments: int, cost_usd: float) -> bool:
        """Record the request and return True if it fits the budget.

        False, recording nothing, if it doesn't or the budget is unreadable.
        """
        try:
            summary = await self.billing_service.get_month_to_date_summary()
        except Exception:
            self.logger.exception("Billing is unreadable; not spending on %s", tier)
            return False

        rate = usd_conversion_rate(summary)
        if summary.budget_amount is None or rate is None:
            self.logger.warning(
                "No budget or currency rate to check %s against (budget %s, "
                "rate %s); not spending on it",
                tier,
                summary.budget_amount,
                summary.usd_conversion_rate,
            )
            return False

        # Locked so two instances cannot both approve the last of the budget.
        async with self.session_maker() as session:
            await session.execute(
                text("SELECT pg_advisory_xact_lock(:key)"), {"key": SPEND_LOCK_KEY}
            )
            pending_usd = await self._pending_usd(session, summary.data_as_of)
            # Credits are stored negative.
            credit_left_usd = max(self.monthly_credit_usd + summary.credits / rate, 0.0)
            uncovered_usd = max(pending_usd + cost_usd - credit_left_usd, 0.0)
            projected = summary.month_to_date_cost + uncovered_usd * rate

            if projected > summary.budget_amount:
                self.logger.info(
                    "%s would bring spend to %.2f %s, over the %.2f budget",
                    tier,
                    projected,
                    summary.currency,
                    summary.budget_amount,
                )
                return False

            session.add(_charge(tier, shipments, cost_usd))
            await session.commit()

        self.logger.info(
            "Approved %s: %d shipments, ~$%.2f USD; spend projected at %.2f of %.2f",
            tier,
            shipments,
            cost_usd,
            projected,
            summary.budget_amount,
        )
        return True

    @staticmethod
    async def _pending_usd(session: AsyncSession, data_as_of: datetime | None) -> float:
        """Estimated cost of this month's charges the export may not show yet."""
        month_start = now_local().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        since = month_start
        if data_as_of is not None:
            since = max(since, data_as_of - EXPORT_LAG)

        total = (
            await session.execute(
                select(
                    func.coalesce(func.sum(RoutingCharge.estimated_cost_usd), 0.0)
                ).where(col(RoutingCharge.created_at) >= since)
            )
        ).scalar_one()
        return float(total)


def _charge(tier: str, shipments: int, cost_usd: float) -> RoutingCharge:
    return RoutingCharge(tier=tier, shipments=shipments, estimated_cost_usd=cost_usd)

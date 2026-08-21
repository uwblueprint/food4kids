"""Route generation that drains each API's free quota before falling back.

Each Google routing API has its own free monthly allowance. Walking them in
quality order — best routes first — and dropping to the next only once the
current one's free room is gone gives the best routes obtainable without
paying. The in-house cluster+sweep is the floor: no quota, always available.

Implements ``RoutingAlgorithmProtocol`` so the generation runner is unchanged;
it sees one algorithm and never learns there were tiers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.models.api_usage import ApiSku
from app.services.implementations.quota_service import fleet_routing_units

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from app.models.location import Location
    from app.schemas.route_generation import RouteGenerationSettings
    from app.services.implementations.quota_service import QuotaService
    from app.services.protocols.routing_algorithm import RoutingAlgorithmProtocol

logger = logging.getLogger(__name__)


@dataclass
class Tier:
    """One rung of the cascade, in quality order.

    ``sku`` is None for tiers that cost nothing, which are therefore always
    available and need no reservation.
    """

    name: str
    algorithm: RoutingAlgorithmProtocol
    sku: ApiSku | None = None
    # Billable units this tier would consume, given (locations, vehicles).
    # Units differ per SKU: Route Optimization bills per shipment, the Routes
    # API per request, so each tier brings its own conversion.
    units_for: Callable[[int, int], int] | None = None


def routes_compute_units(_num_locations: int, num_vehicles: int) -> int:
    """computeRoutes is billed per request, and we issue one per vehicle."""
    return num_vehicles


class CascadingRoutingAlgorithm:
    """Tries each tier in turn, skipping any whose free quota is spent."""

    def __init__(
        self,
        logger_: logging.Logger,
        quota_service: QuotaService,
        session_maker: async_sessionmaker[AsyncSession],
        tiers: list[Tier],
    ) -> None:
        self.logger = logger_
        self.quota_service = quota_service
        self.session_maker = session_maker
        self.tiers = tiers
        # Which tier actually ran. Read by the runner to record on the job, so
        # a silent drop to a lower-quality tier is visible rather than just
        # producing quietly worse routes.
        self.last_tier_used: str | None = None

    async def generate_routes(
        self,
        locations: list[Location],
        warehouse_lat: float,
        warehouse_lon: float,
        settings: RouteGenerationSettings,
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:
        """Generate routes with the best tier that still has free quota."""
        self.last_tier_used = None
        attempts: list[str] = []

        for tier in self.tiers:
            units = self._units_for(tier, len(locations), settings.num_routes)

            if not await self._reserve(tier, units):
                attempts.append(f"{tier.name} (no free quota)")
                continue

            try:
                routes = await tier.algorithm.generate_routes(
                    locations,
                    warehouse_lat,
                    warehouse_lon,
                    settings,
                    timeout_seconds=timeout_seconds,
                )
            except TimeoutError:
                # The request may well have reached Google and been billed, so
                # the reservation stands. Overcounting costs a worse route;
                # undercounting costs money.
                attempts.append(f"{tier.name} (timed out)")
                self.logger.warning(
                    "Tier %s timed out; keeping its reservation and falling back",
                    tier.name,
                )
                continue
            except Exception:
                # Never reached the optimizer — a misconfiguration or a
                # rejected payload. Hand the units back, or a persistently
                # broken tier would burn a month of quota failing.
                await self._release(tier, units)
                attempts.append(f"{tier.name} (failed)")
                self.logger.exception(
                    "Tier %s failed; released its reservation and falling back",
                    tier.name,
                )
                continue

            self.last_tier_used = tier.name
            if attempts:
                self.logger.info(
                    "Generated with %s after skipping: %s",
                    tier.name,
                    ", ".join(attempts),
                )
            return routes

        # Only reachable if every tier is quota-gated, which would mean the
        # free cluster+sweep floor was left out of the cascade.
        raise RuntimeError(
            "No routing tier could run. Tried: "
            + (", ".join(attempts) or "none configured")
        )

    @staticmethod
    def _units_for(tier: Tier, num_locations: int, num_vehicles: int) -> int:
        if tier.sku is None or tier.units_for is None:
            return 0
        return tier.units_for(num_locations, num_vehicles)

    async def _reserve(self, tier: Tier, units: int) -> bool:
        """Claim quota for a tier, in its own committed transaction.

        Separate from the job's session on purpose: Google bills for the call
        whether or not the job later succeeds, so the usage must not roll back
        with it.
        """
        if tier.sku is None:
            return True

        async with self.session_maker() as session:
            granted = await self.quota_service.try_reserve(session, tier.sku, units)
            await session.commit()
            return granted

    async def _release(self, tier: Tier, units: int) -> None:
        if tier.sku is None:
            return

        async with self.session_maker() as session:
            await self.quota_service.release(session, tier.sku, units)
            await session.commit()


def build_default_cascade(
    quota_service: QuotaService,
    session_maker: async_sessionmaker[AsyncSession],
    fleet_routing: RoutingAlgorithmProtocol,
    cluster_sweep: RoutingAlgorithmProtocol,
) -> CascadingRoutingAlgorithm:
    """The Auto cascade: best quality first, free in-house engine last.

    The single-vehicle tier is not wired yet — see F4KRP: the ticket's
    "single-vehicle Routes API" resolves to either Route Optimization's Single
    Vehicle Routing SKU (per shipment, ~1k/month) or Routes API computeRoutes
    (per request, 5-10k/month), which differ by roughly three orders of
    magnitude in usable free room. ``Tier`` takes any number of rungs, so it
    slots in between these two once that is settled.
    """
    return CascadingRoutingAlgorithm(
        logger,
        quota_service,
        session_maker,
        [
            Tier(
                name="fleet_routing",
                algorithm=fleet_routing,
                sku=ApiSku.FLEET_ROUTING,
                units_for=fleet_routing_units,
            ),
            Tier(name="cluster_sweep", algorithm=cluster_sweep),
        ],
    )

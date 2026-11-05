"""Route generation with the best engine the budget allows.

Tiers run in quality order; a paid tier runs only if the spend service approves
it, and any refusal or failure falls to the next. The in-house sweep is free.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.services.implementations.google_maps_routing_service import (
    GoogleMapsFleetRoutingAlgorithm,
)
from app.services.implementations.single_vehicle_routing import (
    SingleVehicleRoutingAlgorithm,
)
from app.services.implementations.sweep_clustering import SweepRoutingAlgorithm

if TYPE_CHECKING:
    from app.models.location import Location
    from app.schemas.route_generation import RouteGenerationSettings
    from app.services.implementations.routing_spend_service import (
        RoutingSpendService,
    )
    from app.services.protocols.routing_algorithm import RoutingAlgorithmProtocol

logger = logging.getLogger(__name__)

# Route Optimization list prices per shipment, first paid volume band
# (https://developers.google.com/maps/billing-and-pricing/pricing). Estimates
# ignore free allowances, which only affects calls the billing export hasn't
# caught up with yet (about a day's worth), and errs toward caution.
FLEET_ROUTING_USD_PER_SHIPMENT = 30.0 / 1000
SINGLE_VEHICLE_USD_PER_SHIPMENT = 10.0 / 1000


@dataclass(frozen=True)
class Tier:
    name: str
    algorithm: RoutingAlgorithmProtocol
    # Every location is one billed shipment. None for the free in-house floor.
    usd_per_shipment: float | None = None


def fleet_routing_tier() -> Tier:
    return Tier(
        name="fleet_routing",
        algorithm=GoogleMapsFleetRoutingAlgorithm(),
        usd_per_shipment=FLEET_ROUTING_USD_PER_SHIPMENT,
    )


def single_vehicle_tier() -> Tier:
    # Single-stop routes skip their request, so this can only overcount.
    return Tier(
        name="single_vehicle",
        algorithm=SingleVehicleRoutingAlgorithm(),
        usd_per_shipment=SINGLE_VEHICLE_USD_PER_SHIPMENT,
    )


def cluster_sweep_tier() -> Tier:
    return Tier(name="cluster_sweep", algorithm=SweepRoutingAlgorithm())


class CascadingRoutingAlgorithm:
    """Tries each tier in turn, skipping any the budget cannot cover."""

    def __init__(self, spend: RoutingSpendService, tiers: list[Tier]) -> None:
        self.spend = spend
        self.tiers = tiers

    async def generate_routes(
        self,
        locations: list[Location],
        warehouse_lat: float,
        warehouse_lon: float,
        settings: RouteGenerationSettings,
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:
        attempts: list[str] = []

        for tier in self.tiers:
            # Nothing is sent yet, so a failed check only costs this tier.
            try:
                approved = await self._approve(tier, len(locations))
            except Exception:
                logger.exception("Could not check spend for tier %s", tier.name)
                attempts.append(f"{tier.name} (spend check failed)")
                continue
            if not approved:
                attempts.append(f"{tier.name} (over budget)")
                continue

            # The charge stands on failure: the request may have been billed.
            try:
                routes = await tier.algorithm.generate_routes(
                    locations,
                    warehouse_lat,
                    warehouse_lon,
                    settings,
                    timeout_seconds=timeout_seconds,
                )
            except Exception as error:
                logger.exception("Tier %s failed; falling back", tier.name)
                attempts.append(f"{tier.name} (failed: {error!r})")
                continue

            if attempts:
                logger.info(
                    "Generated with %s after: %s", tier.name, ", ".join(attempts)
                )
            return routes

        raise RuntimeError("No routing tier could run. Tried: " + ", ".join(attempts))

    async def _approve(self, tier: Tier, num_locations: int) -> bool:
        if tier.usd_per_shipment is None:
            return True
        cost_usd = num_locations * tier.usd_per_shipment
        return await self.spend.try_charge(tier.name, num_locations, cost_usd)

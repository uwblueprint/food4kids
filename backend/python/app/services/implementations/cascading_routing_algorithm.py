"""Route generation that uses the best engine the budget allows.

Tiers run in quality order. A paid tier runs only if the spend service approves
its estimated cost; otherwise, or if it fails, generation falls to the next.
The in-house sweep is the floor: free, so always available.

Implements ``RoutingAlgorithmProtocol`` so the generation runner is unchanged;
it sees one algorithm and never learns there were tiers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.services.implementations.google_maps_routing_service import (
    GoogleMapsFleetRoutingAlgorithm,
    billed_shipments,
)
from app.services.implementations.single_vehicle_routing import (
    SingleVehicleRoutingAlgorithm,
)
from app.services.implementations.sweep_clustering import SweepRoutingAlgorithm

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.models.location import Location
    from app.schemas.route_generation import RouteGenerationSettings
    from app.services.implementations.routing_spend_service import (
        RoutingSpendService,
    )
    from app.services.protocols.routing_algorithm import RoutingAlgorithmProtocol

logger = logging.getLogger(__name__)

# Route Optimization list prices per shipment, first paid volume band
# (https://developers.google.com/maps/billing-and-pricing/pricing). Free
# allowances are ignored, so estimates only ever run high.
FLEET_ROUTING_USD_PER_SHIPMENT = 30.0 / 1000
SINGLE_VEHICLE_USD_PER_SHIPMENT = 10.0 / 1000


@dataclass(frozen=True)
class Pricing:
    usd_per_shipment: float
    # Billed shipments for (locations, routes requested).
    shipments_for: Callable[[int, int], int]


@dataclass(frozen=True)
class Tier:
    name: str
    algorithm: RoutingAlgorithmProtocol
    # None for the free in-house floor.
    pricing: Pricing | None = None


def fleet_routing_tier() -> Tier:
    return Tier(
        name="fleet_routing",
        algorithm=GoogleMapsFleetRoutingAlgorithm(),
        pricing=Pricing(FLEET_ROUTING_USD_PER_SHIPMENT, billed_shipments),
    )


def single_vehicle_tier() -> Tier:
    # One request per route, each with one vehicle. Single-stop routes skip
    # the request, so this can overcount but never undercounts.
    return Tier(
        name="single_vehicle",
        algorithm=SingleVehicleRoutingAlgorithm(),
        pricing=Pricing(
            SINGLE_VEHICLE_USD_PER_SHIPMENT,
            lambda locations, _routes: billed_shipments(locations, 1),
        ),
    )


def cluster_sweep_tier() -> Tier:
    return Tier(name="cluster_sweep", algorithm=SweepRoutingAlgorithm())


class CascadingRoutingAlgorithm:
    """Tries each tier in turn, skipping any the budget cannot cover.

    With ``enforce_budget`` off, paid tiers are recorded but never refused:
    pinning an engine is a deliberate choice to pay for it.
    """

    def __init__(
        self,
        spend: RoutingSpendService,
        tiers: list[Tier],
        enforce_budget: bool = True,
    ) -> None:
        self.spend = spend
        self.tiers = tiers
        self.enforce_budget = enforce_budget

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
            # A database blip while checking spend costs this tier, not the
            # job: nothing has been sent yet, and the free floor needs no check.
            try:
                approved = await self._approve(tier, len(locations), settings)
            except Exception:
                logger.exception("Could not check spend for tier %s", tier.name)
                attempts.append(f"{tier.name} (spend check failed)")
                continue
            if not approved:
                attempts.append(f"{tier.name} (over budget)")
                continue

            # Any failure, a timeout included, falls back. The charge stands:
            # the request may have been billed, and an overestimate only lasts
            # until the billing export catches up.
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

    async def _approve(
        self, tier: Tier, num_locations: int, settings: RouteGenerationSettings
    ) -> bool:
        if tier.pricing is None:
            return True
        shipments = tier.pricing.shipments_for(num_locations, settings.num_routes)
        cost_usd = shipments * tier.pricing.usd_per_shipment
        if not self.enforce_budget:
            await self.spend.charge(tier.name, shipments, cost_usd)
            return True
        return await self.spend.try_charge(tier.name, shipments, cost_usd)

"""Per-driver route ordering via one-vehicle Route Optimization requests.

The middle rung of the generation cascade. Sweep clustering decides which stops
go to which driver, then each driver's stops are ordered by Route Optimization
with a single vehicle. Google bills one-vehicle requests to its Single Vehicle
Routing SKU (5,000 free shipments a month, then a third of Fleet Routing's
price), so this keeps Google's ordering and gives up only its assignment.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from app.services.implementations.google_maps_routing_service import (
    GoogleMapsFleetRoutingAlgorithm,
)
from app.services.implementations.sweep_clustering import SweepRoutingAlgorithm

if TYPE_CHECKING:
    from app.models.location import Location
    from app.schemas.route_generation import RouteGenerationSettings


def _remaining(timeout_seconds: float | None, started: float) -> float | None:
    """What is left of the tier's budget, clamped at zero; None if unbounded."""
    if timeout_seconds is None:
        return None
    return max(timeout_seconds - (time.monotonic() - started), 0.0)


class SingleVehicleRoutingAlgorithm:
    """Clusters in-house, then orders each cluster with Route Optimization."""

    def __init__(self) -> None:
        self.clustering = SweepRoutingAlgorithm()
        self.optimizer = GoogleMapsFleetRoutingAlgorithm()

    async def generate_routes(
        self,
        locations: list[Location],
        warehouse_lat: float,
        warehouse_lon: float,
        settings: RouteGenerationSettings,
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:
        if not locations:
            return []

        started = time.monotonic()
        clusters = await self.clustering.generate_routes(
            locations,
            warehouse_lat,
            warehouse_lon,
            settings,
            timeout_seconds=timeout_seconds,
        )
        one_vehicle = settings.model_copy(update={"num_routes": 1})

        # The tier's own deadline, so a hanging request raises TimeoutError
        # here and the cascade can fall back instead of the job timing out.
        routes = await asyncio.wait_for(
            asyncio.gather(
                *(
                    self._order(cluster, warehouse_lat, warehouse_lon, one_vehicle)
                    for cluster in clusters
                )
            ),
            timeout=_remaining(timeout_seconds, started),
        )
        return list(routes)

    async def _order(
        self,
        cluster: list[Location],
        warehouse_lat: float,
        warehouse_lon: float,
        one_vehicle: RouteGenerationSettings,
    ) -> list[Location]:
        """One cluster in Google's order. Fewer than two stops need no request."""
        if len(cluster) < 2:
            return cluster

        (route,) = await self.optimizer.generate_routes(
            cluster, warehouse_lat, warehouse_lon, one_vehicle
        )

        if sorted(stop.location_id for stop in route) != sorted(
            stop.location_id for stop in cluster
        ):
            raise RuntimeError(
                f"Route Optimization returned {len(route)} of a cluster's "
                f"{len(cluster)} stops."
            )
        return route

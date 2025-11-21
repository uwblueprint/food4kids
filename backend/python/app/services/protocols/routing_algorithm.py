from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.models.location import Location
    from app.schemas.route_generation import RouteGenerationSettings
    from app.services.protocols.clustering_algorithm import ClusteringAlgorithmProtocol


class TimeoutError(Exception):
    """Raised when an operation exceeds its timeout limit."""

    pass


class RoutingAlgorithmProtocol(Protocol):
    """Protocol for routing algorithms.

    Routing algorithms are pure functions that take a list of locations and
    settings, and return multiple routes (each route is a list of locations).
    Algorithms should not interact with the database - they only compute
    the optimal route assignments.

    Algorithms may call external APIs (e.g., for distance calculations) or
    perform long computations, so they are async to allow for efficient
    concurrent operations.
    """

    clustering_algorithm: ClusteringAlgorithmProtocol

    async def generate_routes(
        self,
        locations: list[Location],
        warehouse_lat: float,
        warehouse_lon: float,
        settings: RouteGenerationSettings,
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:  # pragma: no cover - interface only
        """Generate routes from a list of locations.

        Args:
            locations: List of locations to route
            warehouse_lat: Latitude of the warehouse
            warehouse_lon: Longitude of the warehouse
            settings: Route generation settings (num_routes, etc.)
            timeout_seconds: Optional timeout in seconds. If provided, the
                algorithm should raise TimeoutError if execution exceeds this
                duration. If None, no timeout is enforced.

        Returns:
            List of routes, where each route is a list of locations in order

        Raises:
            TimeoutError: If timeout_seconds is provided and execution exceeds
            the timeout duration
        """

        start_time = time.time()

        def check_timeout():
            if timeout_seconds is not None:
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    raise TimeoutError(
                        f"Sweep clustering exceeded timeout of {timeout_seconds}s "
                        f"(elapsed: {elapsed:.2f}s)"
                    )

        # Step 1: Cluster the locations
        clusters = await self.clustering_algorithm.cluster_locations(
            locations=locations,
            num_clusters=settings.num_routes,
            max_locations_per_cluster=getattr(settings, "max_stops_per_route", None),
        )
        check_timeout()

        # Step 2: Generate a route for each cluster
        routes = []
        for cluster in clusters:
            route = self._generate_single_route(cluster, warehouse_lat, warehouse_lon)
            check_timeout()
            routes.append(route)

        return routes

    def _generate_single_route(
        self,
        locations: list[Location],
        warehouse_lat: float,
        warehouse_lon: float,
    ) -> list[Location]:
        """Generate a single route from a cluster of locations.

        Uses angular sweep sorting: sorts locations by their angle from the
        warehouse, then by distance for locations at the same angle.

        Args:
            locations: List of locations in the cluster
            warehouse_lat: Latitude of the warehouse
            warehouse_lon: Longitude of the warehouse

        Returns:
            List of locations in route order
        """
        tau = math.tau

        def calculate_angle_from_warehouse(location: Location) -> float | None:
            if location.latitude is None or location.longitude is None:
                return None
            lat_difference = location.latitude - warehouse_lat
            lon_difference = location.longitude - warehouse_lon
            return math.atan2(lat_difference, lon_difference) % tau

        def calculate_distance_squared(location: Location) -> float | None:
            if location.latitude is None or location.longitude is None:
                return None
            lat_difference = location.latitude - warehouse_lat
            lon_difference = location.longitude - warehouse_lon
            return lon_difference**2 + lat_difference**2

        return sorted(
            locations,
            key=lambda location: (
                calculate_angle_from_warehouse(location),
                calculate_distance_squared(location),
            ),
        )

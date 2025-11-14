from __future__ import annotations

import math
from typing import TYPE_CHECKING, Protocol

from backend.python.app.services.protocols import clustering_algorithm

if TYPE_CHECKING:
    from app.models.location import Location
    from app.schemas.route_generation import RouteGenerationSettings


class RoutingAlgorithmProtocol(Protocol):
    """Protocol for routing algorithms.

    Routing algorithms are pure functions that take a list of locations and
    settings, and return multiple routes (each route is a list of locations).
    Algorithms should not interact with the database - they only compute
    the optimal route assignments.
    """

    def generate_routes(
        self,
        locations: list[Location],
        depot,
        settings: RouteGenerationSettings,
    ) -> list[list[Location]]:  # pragma: no cover - interface only
        """Generate routes from a list of locations.

        Args:
            locations: List of locations to route
            settings: Route generation settings (num_routes, etc.)

        Returns:
            List of routes, where each route is a list of locations in order
        """
        # Step 1: Cluster the locations
        clusters = clustering_algorithm.cluster_locations(
            locations=locations,
            num_clusters=settings.num_routes,
            max_locations_per_cluster=getattr(settings, "max_stops_per_route", None),
        )

        # Step 2: Generate a route for each cluster
        routes = []
        for cluster in clusters:
            route = self._generate_single_route(cluster, depot)
            routes.append(route)

        return routes

    def _generate_single_route(
        self,
        locations: list[Location],
        depot,
    ) -> list[Location]:
        """Generate a single route from a cluster of locations.

        Args:
            locations: List of locations in the cluster
            depot: The depot/warehouse location (tuple of x, y coordinates)

        Returns:
            List of locations in route order
        """
        wx, wy = depot
        tau = math.tau

        def angle(p):
            return math.atan2(p[1] - wy, p[0] - wx) % tau

        return sorted(
            locations,
            key=lambda p: (angle(p), (p[0] - wx) ** 2 + (p[1] - wy) ** 2),
        )

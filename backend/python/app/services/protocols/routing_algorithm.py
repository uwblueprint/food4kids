from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

import math

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
    locations = [(123.2,921), (23.2,32), (585.2,23), (234.2,95421)]
    warehouse = (324.2, 943)
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
        wx, wy = depot
        tau = math.tau

        def angle(p):
            return math.atan2(p[1] - wy, p[0] - wx) % tau

        return sorted(
            locations,
            key=lambda p: (angle(p), (p[0] - wx)**2 + (p[1] - wy)**2),
        )

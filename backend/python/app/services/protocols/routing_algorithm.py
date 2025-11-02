from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

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
        settings: RouteGenerationSettings,
    ) -> list[list[Location]]:  # pragma: no cover - interface only
        """Generate routes from a list of locations.

        Args:
            locations: List of locations to route
            settings: Route generation settings (num_routes, etc.)

        Returns:
            List of routes, where each route is a list of locations in order
        """
        ...

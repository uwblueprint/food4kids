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

    Algorithms may call external APIs (e.g., for distance calculations) or
    perform long computations, so they are async to allow for efficient
    concurrent operations.
    """

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
        ...

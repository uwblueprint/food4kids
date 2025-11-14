from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.implementations.mock_clustering_algorithm import (
    MockClusteringAlgorithm,
)
from app.services.protocols.routing_algorithm import (
    RoutingAlgorithmProtocol,
)

if TYPE_CHECKING:
    from app.models.location import Location
    from app.schemas.route_generation import RouteGenerationSettings


class MockRoutingAlgorithm(RoutingAlgorithmProtocol):
    """Simple mock routing algorithm that uses the mock clustering algorithm."""

    def generate_routes(
        self,
        locations: list[Location],
        settings: RouteGenerationSettings,
    ) -> list[list[Location]]:
        """Split locations evenly across routes using the mock clustering algorithm."""

        clustering_algorithm = MockClusteringAlgorithm()
        return clustering_algorithm.cluster_locations(
            locations=locations,
            num_clusters=settings.num_routes,
            max_locations_per_cluster=settings.max_stops_per_route,
        )

from __future__ import annotations

import requests

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


class GoogleMapsFleetRoutingAlgorithm(RoutingAlgorithmProtocol):
    """Simple mock routing algorithm that uses the mock clustering algorithm."""

    def generate_routes(
        self,
        locations: list[Location],
        warehouse_lat: float,
        warehouse_lng: float,
        settings: RouteGenerationSettings,
    ) -> list[list[Location]]:
        """Split locations evenly across routes using the mock clustering algorithm."""

        vehicles = [
            {
                "vehicleId": f"driver_{i}",
                "startLocation": {"latLng": {"latitude": warehouse_lat, "longitude": warehouse_lng}},
                "capacityLimits": {"load": settings.max_stops_per_route}
            }
            for i in range(settings.num_routes)
        ]

        for i in range(settings.num_routes):
            

        payload = {
            "model":{
                "vehicles": vehicles,
                "shipments": shipments
            }
        }

        requests.post()

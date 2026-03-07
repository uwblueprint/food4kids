"""
Developer script for manually testing the Fleet Routing (optimizeTours) API
with mock locations around Kitchener-Waterloo.

Run from backend/python/:
    docker-compose exec backend pytest scripts/fleet_routing_manual.py -v -s

NOTE: This hits the live Google API and will incur charges.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

import pytest

from app.schemas.route_generation import RouteGenerationSettings
from app.services.implementations.google_maps_routing_service import (
    GoogleMapsFleetRoutingAlgorithm,
)


@dataclass
class FakeLocation:
    latitude: float
    longitude: float
    address: str = ""
    location_id: UUID = field(default_factory=uuid4)


# Sample locations around Kitchener-Waterloo
LOCATIONS = [
    FakeLocation(43.4516, -80.4925, "Kitchener City Hall"),
    FakeLocation(43.4643, -80.5204, "Waterloo Town Square"),
    FakeLocation(43.4506, -80.4983, "Victoria Park"),
    FakeLocation(43.4738, -80.5280, "Uptown Waterloo"),
    FakeLocation(43.4455, -80.4862, "Fairview Park Mall"),
    FakeLocation(43.4380, -80.5050, "Homer Watson Park"),
]

WAREHOUSE_LAT = 43.4500
WAREHOUSE_LON = -80.4900


@pytest.mark.asyncio
async def test_fleet_routing_live() -> None:
    """Hit the live Fleet Routing API and print the resulting routes."""
    from app.config import settings as app_settings

    if not app_settings.route_opt_client_email:
        pytest.skip("ROUTE_OPT_* env vars not configured")

    settings = RouteGenerationSettings(
        num_routes=2,
        max_stops_per_route=4,
        route_start_time=datetime(2025, 6, 1, 9, 0),
        return_to_warehouse=True,
    )

    algo = GoogleMapsFleetRoutingAlgorithm()

    routes = await algo.generate_routes(
        LOCATIONS,  # type: ignore[arg-type]
        WAREHOUSE_LAT,
        WAREHOUSE_LON,
        settings,
    )

    for i, route in enumerate(routes):
        print(f"\nRoute {i + 1} ({len(route)} stops):")
        for stop in route:
            print(f"  - {stop.address} ({stop.latitude}, {stop.longitude})")

    assert len(routes) == 2
    total_stops = sum(len(r) for r in routes)
    assert total_stops == len(LOCATIONS)

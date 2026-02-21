from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.schemas.route_generation import RouteGenerationSettings
from app.services.implementations.google_maps_routing_service import (
    GoogleMapsFleetRoutingAlgorithm,
)


@dataclass
class FakeLocation:
    """Lightweight stand-in for Location that avoids SQLAlchemy mapper init."""

    latitude: float = 43.0
    longitude: float = -79.0
    address: str = "123 Test St"
    location_id: UUID = field(default_factory=uuid4)


@pytest.fixture()
def algorithm() -> GoogleMapsFleetRoutingAlgorithm:
    return GoogleMapsFleetRoutingAlgorithm()


@pytest.fixture()
def make_location() -> Any:
    """Factory that returns FakeLocation instances."""

    def _make(
        latitude: float = 43.0,
        longitude: float = -79.0,
        address: str = "123 Test St",
        location_id: UUID | None = None,
    ) -> FakeLocation:
        return FakeLocation(
            latitude=latitude,
            longitude=longitude,
            address=address,
            location_id=location_id or uuid4(),
        )

    return _make


@pytest.fixture()
def sample_settings() -> RouteGenerationSettings:
    return RouteGenerationSettings(
        num_routes=2,
        max_stops_per_route=5,
        route_start_time=datetime(2025, 1, 1, 9, 0),
    )


# ---------------------------------------------------------------------------
# _build_payload
# ---------------------------------------------------------------------------


class TestBuildPayload:
    def test_basic_payload_structure(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
        sample_settings: RouteGenerationSettings,
    ) -> None:
        """2 locations, 2 routes, max_stops=5 — verify v1 field names."""
        locs = [
            make_location(latitude=43.1, longitude=-79.1),
            make_location(latitude=43.2, longitude=-79.2),
        ]

        payload = algorithm._build_payload(locs, 43.0, -79.0, sample_settings)

        model = payload["model"]

        # --- vehicles ---
        vehicles = model["vehicles"]
        assert len(vehicles) == 2
        for i, v in enumerate(vehicles):
            assert v["displayName"] == f"driver_{i}"
            assert v["startLocation"] == {"latitude": 43.0, "longitude": -79.0}
            assert v["loadLimits"] == {"load": {"maxLoad": "5"}}

        # --- shipments = forced_pickups + deliveries ---
        shipments = model["shipments"]
        assert len(shipments) == 4  # 2 forced pickups + 2 deliveries

        # forced pickups (no loadDemands — demand is 0 to preserve capacity)
        for i in range(2):
            fp = shipments[i]
            assert fp["displayName"] == f"initial_load_driver_{i}"
            pickup = fp["pickups"][0]
            assert pickup["arrivalLocation"] == {"latitude": 43.0, "longitude": -79.0}
            assert "loadDemands" not in pickup
            assert fp["allowedVehicleIndices"] == [i]

        # deliveries
        for idx, loc in enumerate(locs):
            d = shipments[2 + idx]
            assert d["displayName"] == f"ship_{idx}"
            delivery = d["deliveries"][0]
            assert delivery["arrivalLocation"] == {
                "latitude": loc.latitude,
                "longitude": loc.longitude,
            }
            assert delivery["loadDemands"] == {"load": {"amount": "1"}}

    def test_return_to_warehouse_sets_end_location(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
    ) -> None:
        """When return_to_warehouse is True, vehicles get endLocation."""
        settings = RouteGenerationSettings(
            num_routes=1,
            max_stops_per_route=5,
            route_start_time=datetime(2025, 1, 1, 9, 0),
            return_to_warehouse=True,
        )
        locs = [make_location()]

        payload = algorithm._build_payload(locs, 43.0, -79.0, settings)

        vehicle = payload["model"]["vehicles"][0]
        assert vehicle["endLocation"] == {"latitude": 43.0, "longitude": -79.0}

    def test_no_return_to_warehouse_omits_end_location(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
        sample_settings: RouteGenerationSettings,
    ) -> None:
        """When return_to_warehouse is False (default), no endLocation."""
        locs = [make_location()]

        payload = algorithm._build_payload(locs, 43.0, -79.0, sample_settings)

        vehicle = payload["model"]["vehicles"][0]
        assert "endLocation" not in vehicle

    def test_no_max_stops_omits_load_fields(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
    ) -> None:
        """When max_stops_per_route is None, loadLimits / loadDemands are omitted."""
        settings = RouteGenerationSettings(
            num_routes=2,
            max_stops_per_route=None,
            route_start_time=datetime(2025, 1, 1, 9, 0),
        )
        locs = [make_location()]

        payload = algorithm._build_payload(locs, 43.0, -79.0, settings)

        model = payload["model"]

        # vehicles should NOT have loadLimits
        for v in model["vehicles"]:
            assert "loadLimits" not in v

        # forced pickups should NOT have loadDemands
        for fp in model["shipments"][:2]:
            pickup = fp["pickups"][0]
            assert "loadDemands" not in pickup


# ---------------------------------------------------------------------------
# _parse_response
# ---------------------------------------------------------------------------


class TestParseResponse:
    def test_standard_response(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
    ) -> None:
        """3 locations split across 2 vehicles — verify grouping and order."""
        locs = [make_location(address=f"Loc {i}") for i in range(3)]
        num_routes = 2

        response = {
            "routes": [
                {
                    "vehicleIndex": 0,
                    "visits": [
                        {"shipmentIndex": 0, "isPickup": True},  # forced pickup
                        {"shipmentIndex": 2},  # locs[0]
                        {"shipmentIndex": 4},  # locs[2]
                    ],
                },
                {
                    "vehicleIndex": 1,
                    "visits": [
                        {"shipmentIndex": 1, "isPickup": True},  # forced pickup
                        {"shipmentIndex": 3},  # locs[1]
                    ],
                },
            ]
        }

        routes = algorithm._parse_response(response, locs, num_routes)

        assert len(routes) == 2
        assert routes[0] == [locs[0], locs[2]]
        assert routes[1] == [locs[1]]

    def test_skips_pickup_visits(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
    ) -> None:
        """Visits with isPickup=True are excluded from routes."""
        locs = [make_location()]
        num_routes = 1

        response = {
            "routes": [
                {
                    "vehicleIndex": 0,
                    "visits": [
                        {"shipmentIndex": 0, "isPickup": True},
                        {"shipmentIndex": 1},  # locs[0]
                    ],
                }
            ]
        }

        routes = algorithm._parse_response(response, locs, num_routes)

        assert len(routes) == 1
        assert routes[0] == [locs[0]]

    def test_empty_response(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
    ) -> None:
        """No routes in response returns list of empty lists."""
        locs = [make_location()]
        num_routes = 2

        routes = algorithm._parse_response({}, locs, num_routes)

        assert routes == [[], []]


# ---------------------------------------------------------------------------
# generate_routes (end-to-end with mocked API)
# ---------------------------------------------------------------------------


class TestGenerateRoutes:
    @pytest.mark.asyncio
    async def test_empty_locations_returns_immediately(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        sample_settings: RouteGenerationSettings,
        mocker: Any,
    ) -> None:
        """Empty locations list returns [] without calling the API."""
        spy = mocker.patch.object(algorithm, "_call_api")

        result = await algorithm.generate_routes([], 43.0, -79.0, sample_settings)

        assert result == []
        spy.assert_not_called()

    @pytest.mark.asyncio
    async def test_successful_call(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
        sample_settings: RouteGenerationSettings,
        mocker: Any,
    ) -> None:
        """Mock _call_api and verify locations are grouped into routes."""
        locs = [make_location(address=f"Stop {i}") for i in range(3)]

        fake_response = {
            "routes": [
                {
                    "vehicleIndex": 0,
                    "visits": [
                        {"shipmentIndex": 0, "isPickup": True},
                        {"shipmentIndex": 2},  # locs[0]
                    ],
                },
                {
                    "vehicleIndex": 1,
                    "visits": [
                        {"shipmentIndex": 1, "isPickup": True},
                        {"shipmentIndex": 3},  # locs[1]
                        {"shipmentIndex": 4},  # locs[2]
                    ],
                },
            ]
        }

        mocker.patch.object(algorithm, "_call_api", return_value=fake_response)

        routes = await algorithm.generate_routes(locs, 43.0, -79.0, sample_settings)

        assert len(routes) == 2
        assert routes[0] == [locs[0]]
        assert routes[1] == [locs[1], locs[2]]

    @pytest.mark.asyncio
    async def test_timeout_raises(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
        sample_settings: RouteGenerationSettings,
        mocker: Any,
    ) -> None:
        """When _call_api is slow and timeout is tiny, asyncio.TimeoutError is raised."""

        def slow_api(_payload: dict) -> dict:
            time.sleep(2)
            return {}

        mocker.patch.object(algorithm, "_call_api", side_effect=slow_api)

        with pytest.raises(asyncio.TimeoutError):
            await algorithm.generate_routes(
                [make_location()],
                43.0,
                -79.0,
                sample_settings,
                timeout_seconds=0.01,
            )

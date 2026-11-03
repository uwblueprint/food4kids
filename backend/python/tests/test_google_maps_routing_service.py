from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.config import settings as app_settings
from app.schemas.route_generation import RouteGenerationSettings
from app.services.implementations.google_maps_routing_service import (
    GLOBAL_HORIZON_HOURS,
    MANDATORY_DELIVERY_PENALTY,
    OVER_TARGET_COST_PER_HOUR,
    OVER_TARGET_COST_PER_SQUARE_HOUR,
    QUADRATIC_TARGET_FACTOR,
    SCOPES,
    STRAIGHT_LINE_KMH,
    VEHICLE_COST_PER_HOUR,
    GoogleMapsFleetRoutingAlgorithm,
    _target_route_seconds,
)

# Degrees of latitude per km (and of longitude per km at the equator).
DEGREES_PER_KM = 1 / 111.195


@dataclass
class FakeLocation:
    """Lightweight stand-in for Location that avoids SQLAlchemy mapper init."""

    latitude: float = 43.0
    longitude: float = -79.0
    address: str = "123 Test St"
    location_id: UUID = field(default_factory=uuid4)
    num_children: int = 2


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
        num_children: int = 2,
    ) -> FakeLocation:
        return FakeLocation(
            latitude=latitude,
            longitude=longitude,
            address=address,
            location_id=location_id or uuid4(),
            num_children=num_children,
        )

    return _make


# The three configured numbers have no schema defaults, so every settings
# object in this file states them. These stand in for a system_settings row.
CONFIGURED_BOXES_PER_CAR = 10
CONFIGURED_CHILDREN_PER_BOX = 2
CONFIGURED_DROPOFF_MINUTES = 3


def _settings(**overrides: Any) -> RouteGenerationSettings:
    base: dict[str, Any] = {
        "num_routes": 1,
        "route_start_time": datetime(2025, 1, 1, 9, 0),
        "max_boxes_per_driver": CONFIGURED_BOXES_PER_CAR,
        "children_per_box": CONFIGURED_CHILDREN_PER_BOX,
        "service_time_minutes": CONFIGURED_DROPOFF_MINUTES,
    }
    return RouteGenerationSettings(**{**base, **overrides})


@pytest.fixture()
def sample_settings() -> RouteGenerationSettings:
    return _settings(num_routes=2)


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
        """2 locations, 2 routes — verify v1 field names."""
        locs = [
            make_location(latitude=43.1, longitude=-79.1),
            make_location(latitude=43.2, longitude=-79.2),
        ]

        payload = algorithm._build_payload(locs, 43.0, -79.0, sample_settings)

        model = payload["model"]
        target = _target_route_seconds(locs, 43.0, -79.0, sample_settings)

        # --- vehicles ---
        vehicles = model["vehicles"]
        assert len(vehicles) == 2
        for i, v in enumerate(vehicles):
            assert v == {
                "displayName": f"driver_{i}",
                "startLocation": {"latitude": 43.0, "longitude": -79.0},
                "usedIfRouteIsEmpty": True,
                "loadLimits": {
                    "load": {"maxLoad": str(sample_settings.max_boxes_per_driver)},
                    # Leaves with at least one stop, returns with none.
                    "stops": {
                        "startLoadInterval": {"min": "1"},
                        "endLoadInterval": {"max": "0"},
                    },
                },
                "costPerHour": VEHICLE_COST_PER_HOUR,
                "routeDurationLimit": {
                    "maxDuration": f"{GLOBAL_HORIZON_HOURS * 3600}s",
                    "softMaxDuration": f"{target}s",
                    "costPerHourAfterSoftMax": OVER_TARGET_COST_PER_HOUR,
                    "quadraticSoftMaxDuration": f"{round(target * 1.3)}s",
                    "costPerSquareHourAfterQuadraticSoftMax": (
                        OVER_TARGET_COST_PER_SQUARE_HOUR
                    ),
                },
            }

        # Spreading the work is priced per route, not by the plan's span.
        assert "globalDurationCostPerHour" not in model

        # --- shipments: one delivery per location, in order ---
        shipments = model["shipments"]
        assert len(shipments) == 2

        for idx, loc in enumerate(locs):
            d = shipments[idx]
            assert d["displayName"] == f"ship_{idx}"
            assert d["penaltyCost"] == MANDATORY_DELIVERY_PENALTY
            delivery = d["deliveries"][0]
            assert delivery["arrivalLocation"] == {
                "latitude": loc.latitude,
                "longitude": loc.longitude,
            }
            # Demand is the derived box count, not raw children:
            # ceil(2 children / 2 per box) = 1 box.
            assert delivery["loadDemands"] == {
                "load": {"amount": "1"},
                "stops": {"amount": "1"},
            }

    def test_global_start_time_anchors_the_model(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
        sample_settings: RouteGenerationSettings,
    ) -> None:
        """route_start_time lands on model.globalStartTime, not on the vehicles.

        A Vehicle has no scalar start time (only startTimeWindows), so a
        timestamp put there is silently dropped by the API.
        """
        payload = algorithm._build_payload(
            [make_location()], 43.0, -79.0, sample_settings
        )
        model = payload["model"]

        # January 1st is outside DST, so America/New_York is UTC-5 here.
        assert model["globalStartTime"] == "2025-01-01T09:00:00-05:00"
        for vehicle in model["vehicles"]:
            assert "startTime" not in vehicle

    def test_global_end_time_is_always_sent_and_after_the_start(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
        sample_settings: RouteGenerationSettings,
    ) -> None:
        """globalEndTime must be present and later than globalStartTime.

        Omitting it defaults the field to the epoch, and the API rejects every
        request with "`global_start_time` after `global_end_time`".
        """
        model = algorithm._build_payload(
            [make_location()], 43.0, -79.0, sample_settings
        )["model"]

        assert "globalEndTime" in model
        start = datetime.fromisoformat(model["globalStartTime"])
        end = datetime.fromisoformat(model["globalEndTime"])
        assert end > start
        assert end - start == timedelta(hours=GLOBAL_HORIZON_HOURS)

    def test_global_end_time_spans_a_full_day_of_slack(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
    ) -> None:
        """The horizon is wide enough that a long day can never overrun it."""
        settings = _settings(
            num_routes=1,
            route_start_time=datetime(2026, 7, 9, 8, 30),
        )

        model = algorithm._build_payload([make_location()], 43.0, -79.0, settings)[
            "model"
        ]

        assert model["globalStartTime"] == "2026-07-09T08:30:00-04:00"
        assert model["globalEndTime"] == "2026-07-10T08:30:00-04:00"

    def test_global_end_time_follows_an_explicit_offset(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
    ) -> None:
        """A tz-aware start keeps its own offset on both ends of the window."""
        settings = _settings(
            num_routes=1,
            route_start_time=datetime(2025, 1, 1, 14, 0, tzinfo=timezone.utc),
        )

        model = algorithm._build_payload([make_location()], 43.0, -79.0, settings)[
            "model"
        ]

        assert model["globalStartTime"] == "2025-01-01T14:00:00+00:00"
        assert model["globalEndTime"] == "2025-01-02T14:00:00+00:00"

    def test_global_start_time_keeps_the_drive_date(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
    ) -> None:
        """The date half of route_start_time reaches the API, not just the time.

        The optimizer plans against the timestamp's day, so a settings object
        built for July must not come out anchored to some other date.
        """
        settings = _settings(
            num_routes=1,
            route_start_time=datetime(2026, 7, 9, 8, 30),
        )

        payload = algorithm._build_payload([make_location()], 43.0, -79.0, settings)

        # July is DST, so the offset shifts to UTC-4 — same wall clock, and the
        # date is carried through untouched.
        assert payload["model"]["globalStartTime"] == "2026-07-09T08:30:00-04:00"

    def test_global_start_time_preserves_an_explicit_offset(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
    ) -> None:
        """A tz-aware route_start_time is passed through, not re-stamped."""
        settings = _settings(
            num_routes=1,
            route_start_time=datetime(2025, 1, 1, 14, 0, tzinfo=timezone.utc),
        )

        payload = algorithm._build_payload([make_location()], 43.0, -79.0, settings)

        assert payload["model"]["globalStartTime"] == "2025-01-01T14:00:00+00:00"

    def test_service_duration_on_deliveries(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
    ) -> None:
        """Deliveries include duration based on service_time_minutes."""
        settings = _settings(
            num_routes=1,
            route_start_time=datetime(2025, 1, 1, 9, 0),
            service_time_minutes=10,
        )
        locs = [make_location()]

        payload = algorithm._build_payload(locs, 43.0, -79.0, settings)

        delivery = payload["model"]["shipments"][0]["deliveries"][0]
        assert delivery["duration"] == "600s"  # 10 min * 60

    @pytest.mark.parametrize("num_routes", [1, 2, 12])
    def test_one_shipment_per_location_for_any_fleet_size(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
        num_routes: int,
    ) -> None:
        """Every location is one shipment, however many vehicles there are."""
        settings = _settings(num_routes=num_routes)
        locs = [make_location() for _ in range(5)]

        shipments = algorithm._build_payload(locs, 43.0, -79.0, settings)["model"][
            "shipments"
        ]

        assert len(shipments) == len(locs)
        assert all(
            set(s) == {"displayName", "penaltyCost", "deliveries"} for s in shipments
        )

    def test_return_to_warehouse_sets_end_location(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
    ) -> None:
        """When return_to_warehouse is True, vehicles get endLocation."""
        settings = _settings(
            num_routes=1,
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

    def test_location_with_no_children_is_still_a_stop(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
        sample_settings: RouteGenerationSettings,
    ) -> None:
        """Routes are forced out by stops, not boxes, so a route of only
        zero-box locations still counts as delivering something."""
        locs = [make_location(num_children=0)]

        payload = algorithm._build_payload(locs, 43.0, -79.0, sample_settings)

        delivery = payload["model"]["shipments"][0]["deliveries"][0]
        assert delivery["loadDemands"] == {
            "load": {"amount": "0"},
            "stops": {"amount": "1"},
        }

    def test_time_over_target_costs_more_than_driving(self) -> None:
        """Overrunning the target must cost more than an hour of driving, or
        the optimizer would never add driving to even out the routes."""
        assert OVER_TARGET_COST_PER_HOUR > VEHICLE_COST_PER_HOUR
        assert OVER_TARGET_COST_PER_SQUARE_HOUR > 0
        assert QUADRATIC_TARGET_FACTOR > 1

    def test_oversized_location_demand_clamped_to_capacity(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
        sample_settings: RouteGenerationSettings,
    ) -> None:
        """A location over vehicle capacity is clamped to exactly the capacity,
        saturating one vehicle so it gets a dedicated route (the van case)."""
        cap_boxes = sample_settings.max_boxes_per_driver
        # (cap + 4) boxes worth of children, at children_per_box=2
        locs = [make_location(num_children=(cap_boxes + 4) * 2)]

        payload = algorithm._build_payload(locs, 43.0, -79.0, sample_settings)

        delivery = payload["model"]["shipments"][0]["deliveries"][0]
        assert delivery["loadDemands"]["load"] == {"amount": str(cap_boxes)}

    def test_demand_at_capacity_not_clamped(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
        sample_settings: RouteGenerationSettings,
    ) -> None:
        """A location exactly at vehicle capacity passes through unchanged."""
        cap_boxes = sample_settings.max_boxes_per_driver
        locs = [make_location(num_children=cap_boxes * 2)]

        payload = algorithm._build_payload(locs, 43.0, -79.0, sample_settings)

        delivery = payload["model"]["shipments"][0]["deliveries"][0]
        assert delivery["loadDemands"]["load"] == {"amount": str(cap_boxes)}

    def test_demand_below_capacity_rounds_up_to_whole_boxes(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
        sample_settings: RouteGenerationSettings,
    ) -> None:
        """A normal location demands its box count, with partial boxes
        rounded up: 5 children at 2 per box is 3 boxes, not 2.5."""
        locs = [make_location(num_children=5)]

        payload = algorithm._build_payload(locs, 43.0, -79.0, sample_settings)

        delivery = payload["model"]["shipments"][0]["deliveries"][0]
        assert delivery["loadDemands"]["load"] == {"amount": "3"}

    def test_custom_children_per_box(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
    ) -> None:
        """Box derivation honours a non-default children_per_box."""
        settings = _settings(
            num_routes=1,
            route_start_time=datetime(2025, 1, 1, 9, 0),
            children_per_box=3,
        )
        locs = [make_location(num_children=7)]  # ceil(7 / 3) = 3 boxes

        payload = algorithm._build_payload(locs, 43.0, -79.0, settings)

        delivery = payload["model"]["shipments"][0]["deliveries"][0]
        assert delivery["loadDemands"]["load"] == {"amount": "3"}


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
                    "visits": [{"shipmentIndex": 2}, {"shipmentIndex": 0}],
                },
                {
                    "vehicleIndex": 1,
                    "visits": [{"shipmentIndex": 1}],
                },
            ]
        }

        routes = algorithm._parse_response(response, locs, num_routes)

        assert len(routes) == 2
        assert routes[0] == [locs[2], locs[0]]
        assert routes[1] == [locs[1]]

    def test_omitted_indices_are_zero(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
    ) -> None:
        """JSON drops proto3 zero values: no vehicleIndex/shipmentIndex means 0."""
        locs = [make_location(address="a"), make_location(address="b")]

        response = {"routes": [{"visits": [{"shipmentIndex": 1}, {}]}]}

        routes = algorithm._parse_response(response, locs, num_routes=1)

        assert routes == [[locs[1], locs[0]]]

    @pytest.mark.parametrize("shipment_index", [-1, 2, 99])
    def test_unknown_shipment_raises(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
        shipment_index: int,
    ) -> None:
        """A shipment index we never sent fails loudly instead of dropping a stop."""
        locs = [make_location(), make_location()]

        response = {
            "routes": [
                {"vehicleIndex": 0, "visits": [{"shipmentIndex": shipment_index}]}
            ]
        }

        with pytest.raises(RuntimeError, match=f"shipment {shipment_index}"):
            algorithm._parse_response(response, locs, num_routes=1)

    @pytest.mark.parametrize("vehicle_index", [-1, 2, 99])
    def test_unknown_vehicle_raises(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
        vehicle_index: int,
    ) -> None:
        """A vehicle index we never sent fails loudly instead of dropping a route."""
        locs = [make_location()]

        response = {
            "routes": [
                {"vehicleIndex": vehicle_index, "visits": [{"shipmentIndex": 0}]}
            ]
        }

        with pytest.raises(RuntimeError, match=f"vehicle {vehicle_index}"):
            algorithm._parse_response(response, locs, num_routes=2)

    @pytest.mark.parametrize(
        "visits",
        [
            [],  # nothing visited
            [{"shipmentIndex": 0}],  # one location missing
            [{"shipmentIndex": 0}, {"shipmentIndex": 0}, {"shipmentIndex": 1}],
        ],
    )
    def test_every_location_exactly_once(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
        visits: list[dict],
    ) -> None:
        """A missing or repeated stop fails loudly rather than reaching a route."""
        locs = [make_location(), make_location()]

        response = {"routes": [{"vehicleIndex": 0, "visits": visits}]}

        with pytest.raises(RuntimeError, match="exactly once"):
            algorithm._parse_response(response, locs, num_routes=1)

    def test_empty_response_raises(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
    ) -> None:
        """No routes at all for real locations is an error, not empty routes."""
        with pytest.raises(RuntimeError, match="exactly once"):
            algorithm._parse_response({}, [make_location()], num_routes=2)

    def test_skipped_shipments_raises(
        self,
        algorithm: GoogleMapsFleetRoutingAlgorithm,
        make_location: Any,
    ) -> None:
        """If the API skips any shipments, raise RuntimeError."""
        locs = [make_location()]
        num_routes = 1

        response = {
            "routes": [],
            "skippedShipments": [{"index": 1, "label": "ship_0"}],
        }

        with pytest.raises(RuntimeError, match="skipped 1 shipments"):
            algorithm._parse_response(response, locs, num_routes)


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
                    "visits": [{"shipmentIndex": 0}],
                },
                {
                    "vehicleIndex": 1,
                    "visits": [{"shipmentIndex": 1}, {"shipmentIndex": 2}],
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


class TestEnsureCredentials:
    """Credentials come from Application Default Credentials, never from settings."""

    @pytest.fixture(autouse=True)
    def _configured_project(self, mocker: Any) -> None:
        mocker.patch.object(app_settings, "route_opt_project_id", "f4k-test-project")

    def test_fetches_from_adc_and_refreshes(
        self, algorithm: GoogleMapsFleetRoutingAlgorithm, mocker: Any
    ) -> None:
        credentials = mocker.Mock(valid=False)
        default = mocker.patch(
            "app.services.implementations.google_maps_routing_service."
            "google.auth.default",
            return_value=(credentials, "f4k-test-project"),
        )

        result = algorithm._ensure_credentials()

        # Mock assertions first: `assert x is credentials` narrows the Mock to
        # the real Credentials type, after which mypy rejects .assert_called_*.
        default.assert_called_once_with(scopes=SCOPES)
        credentials.refresh.assert_called_once()
        assert result is credentials

    def test_caches_while_valid(
        self, algorithm: GoogleMapsFleetRoutingAlgorithm, mocker: Any
    ) -> None:
        """A valid cached credential is reused without touching ADC again."""
        credentials = mocker.Mock(valid=True)
        default = mocker.patch(
            "app.services.implementations.google_maps_routing_service."
            "google.auth.default",
            return_value=(credentials, "f4k-test-project"),
        )

        first = algorithm._ensure_credentials()
        second = algorithm._ensure_credentials()

        default.assert_called_once()
        # Refreshed once on creation; the cached hit is free.
        credentials.refresh.assert_called_once()
        assert first is second is credentials

    def test_refreshes_expired_without_refetching(
        self, algorithm: GoogleMapsFleetRoutingAlgorithm, mocker: Any
    ) -> None:
        """An expired credential refreshes in place rather than re-resolving ADC."""
        credentials = mocker.Mock(valid=False)
        default = mocker.patch(
            "app.services.implementations.google_maps_routing_service."
            "google.auth.default",
            return_value=(credentials, "f4k-test-project"),
        )

        algorithm._ensure_credentials()
        algorithm._ensure_credentials()

        default.assert_called_once()
        assert credentials.refresh.call_count == 2

    def test_unconfigured_project_raises(
        self, algorithm: GoogleMapsFleetRoutingAlgorithm, mocker: Any
    ) -> None:
        """Fail loudly rather than calling optimizeTours against an empty project."""
        mocker.patch.object(app_settings, "route_opt_project_id", "")
        default = mocker.patch(
            "app.services.implementations.google_maps_routing_service."
            "google.auth.default",
        )

        with pytest.raises(RuntimeError, match="ROUTE_OPT_PROJECT_ID"):
            algorithm._ensure_credentials()

        default.assert_not_called()


# ---------------------------------------------------------------------------
# _target_route_seconds
# ---------------------------------------------------------------------------


def _hours_to_seconds(km: float) -> float:
    return km / STRAIGHT_LINE_KMH * 3600


class TestTargetRouteSeconds:
    SERVICE = CONFIGURED_DROPOFF_MINUTES * 60

    def test_stop_at_the_warehouse_is_only_its_drop_off(
        self, make_location: Any
    ) -> None:
        locs = [make_location(latitude=0.0, longitude=0.0)]
        assert _target_route_seconds(locs, 0.0, 0.0, _settings()) == self.SERVICE

    @pytest.mark.parametrize(("return_to_warehouse", "legs"), [(True, 2), (False, 1)])
    def test_one_far_stop_drives_out_and_maybe_back(
        self, make_location: Any, return_to_warehouse: bool, legs: int
    ) -> None:
        locs = [make_location(latitude=10 * DEGREES_PER_KM, longitude=0.0)]
        settings = _settings(return_to_warehouse=return_to_warehouse)

        target = _target_route_seconds(locs, 0.0, 0.0, settings)

        assert target == pytest.approx(
            _hours_to_seconds(10 * legs) + self.SERVICE, abs=1
        )

    def test_more_routes_split_the_same_work_per_route(
        self, make_location: Any
    ) -> None:
        """Each route makes its own depot legs, so doubling stops and routes
        together keeps the per-route target when the stops share a spot."""
        far = 10 * DEGREES_PER_KM
        one = [make_location(latitude=far, longitude=0.0)]
        two = [make_location(latitude=far, longitude=0.0) for _ in range(2)]

        assert _target_route_seconds(
            one, 0.0, 0.0, _settings(num_routes=1, return_to_warehouse=True)
        ) == _target_route_seconds(
            two, 0.0, 0.0, _settings(num_routes=2, return_to_warehouse=True)
        )

    def test_spread_out_stops_add_the_area_term(self, make_location: Any) -> None:
        """Stops 1 km north and 1 km east: mean depot distance 1 km and a
        1 km x 1 km bounding box, so 2 * 1 + 0.57 * sqrt(2 * 1) km."""
        locs = [
            make_location(latitude=DEGREES_PER_KM, longitude=0.0),
            make_location(latitude=0.0, longitude=DEGREES_PER_KM),
        ]
        settings = _settings(return_to_warehouse=True)

        target = _target_route_seconds(locs, 0.0, 0.0, settings)

        expected_km = 2 * 1 + 0.57 * (2 * 1) ** 0.5
        assert target == pytest.approx(
            _hours_to_seconds(expected_km) + 2 * self.SERVICE, abs=1
        )

    @pytest.mark.parametrize("missing", ["latitude", "longitude"])
    def test_ungeocoded_location_raises(self, make_location: Any, missing: str) -> None:
        loc = make_location()
        setattr(loc, missing, None)

        with pytest.raises(ValueError, match="geocoded"):
            _target_route_seconds([loc], 0.0, 0.0, _settings())

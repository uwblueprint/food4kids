"""Tests for the Routes API single-vehicle ordering tier.

Ordering is the cheap half of route generation: our clustering already decided
who goes where, so the failure that matters here is losing or duplicating a
stop while reordering, which would silently drop a delivery.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.config import settings
from app.schemas.route_generation import RouteGenerationSettings
from app.services.implementations.routes_api_routing_service import (
    MAX_INTERMEDIATES,
    RoutesApiRoutingError,
    RoutesApiSingleVehicleAlgorithm,
)

pytestmark = pytest.mark.asyncio


@dataclass
class FakeLocation:
    """Lightweight stand-in for Location that avoids SQLAlchemy mapper init."""

    latitude: float = 43.0
    longitude: float = -79.0
    address: str = "123 Test St"
    location_id: UUID = field(default_factory=uuid4)
    num_children: int = 2


def _algorithm() -> RoutesApiSingleVehicleAlgorithm:
    return RoutesApiSingleVehicleAlgorithm(
        warehouse_lat=43.4, warehouse_lon=-80.5, children_per_box=2
    )


def _settings(num_routes: int = 2, return_to_warehouse: bool = True) -> Any:
    return RouteGenerationSettings(
        route_start_time=datetime(2026, 9, 2, 8, 0),
        num_routes=num_routes,
        return_to_warehouse=return_to_warehouse,
    )


class TestOrderCluster:
    """A cluster comes back reordered, whole, and in Google's order."""

    async def test_applies_the_returned_order(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        algorithm = _algorithm()
        cluster = [FakeLocation(address=str(i)) for i in range(4)]

        async def fake_order(*_args: Any, **_kwargs: Any) -> list[int]:
            return [2, 0, 3, 1]

        monkeypatch.setattr(algorithm, "_request_order", fake_order)

        ordered = await algorithm._order_cluster(cluster, 43.4, -80.5, True)  # type: ignore[arg-type]

        assert [loc.address for loc in ordered] == ["2", "0", "3", "1"]

    async def test_a_single_stop_needs_no_call(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Nothing to optimise, so the request would spend quota for nothing."""
        algorithm = _algorithm()
        called = False

        async def fake_order(*_args: Any, **_kwargs: Any) -> list[int]:
            nonlocal called
            called = True
            return [0]

        monkeypatch.setattr(algorithm, "_request_order", fake_order)

        ordered = await algorithm._order_cluster([FakeLocation()], 43.4, -80.5, True)  # type: ignore[list-item]

        assert len(ordered) == 1
        assert not called

    async def test_an_empty_cluster_needs_no_call(self) -> None:
        assert await _algorithm()._order_cluster([], 43.4, -80.5, True) == []

    async def test_rejects_a_cluster_over_the_waypoint_limit(self) -> None:
        """Silently truncating would drop deliveries."""
        oversized = [FakeLocation() for _ in range(MAX_INTERMEDIATES + 1)]

        with pytest.raises(RoutesApiRoutingError, match="waypoint limit"):
            await _algorithm()._order_cluster(oversized, 43.4, -80.5, True)  # type: ignore[arg-type]


class TestGenerateRoutes:
    """Every stop that goes in must come out, exactly once."""

    async def test_preserves_every_stop_across_clusters(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        algorithm = _algorithm()
        locations = [FakeLocation(address=str(i)) for i in range(8)]

        async def fake_cluster(**kwargs: Any) -> list[list[Any]]:
            locs = kwargs["locations"]
            return [locs[:4], locs[4:]]

        async def fake_order(cluster: list[Any], *_args: Any) -> list[int]:
            return list(reversed(range(len(cluster))))

        monkeypatch.setattr(
            algorithm.clustering_algorithm, "cluster_locations", fake_cluster
        )
        monkeypatch.setattr(algorithm, "_request_order", fake_order)

        routes = await algorithm.generate_routes(
            locations,  # type: ignore[arg-type]
            43.4,
            -80.5,
            _settings(),
        )

        returned = [loc.address for route in routes for loc in route]
        assert sorted(returned) == sorted(loc.address for loc in locations)

    async def test_no_locations_makes_no_calls(self) -> None:
        assert await _algorithm().generate_routes([], 43.4, -80.5, _settings()) == []


class TestUnusableResponse:
    """A bad ordering must never cost a delivery."""

    async def test_a_short_order_falls_back_to_the_original(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Google returning fewer indices than stops would drop the rest."""
        algorithm = _algorithm()
        cluster = [FakeLocation(address=str(i)) for i in range(4)]

        @dataclass
        class _Route:
            optimized_intermediate_waypoint_index: list[int] = field(
                default_factory=lambda: [0, 1]
            )

        @dataclass
        class _Response:
            routes: list[Any] = field(default_factory=lambda: [_Route()])

        async def fake_compute(*_args: Any, **_kwargs: Any) -> Any:
            return _Response()

        monkeypatch.setattr(settings, "google_maps_api_key", "test-key")
        monkeypatch.setattr(
            "app.services.implementations.routes_api_routing_service."
            "routing_v2.RoutesAsyncClient",
            lambda **_kw: type(
                "C", (), {"compute_routes": staticmethod(fake_compute)}
            )(),
        )

        order = await algorithm._request_order(cluster, 43.4, -80.5, True)  # type: ignore[arg-type]

        assert order == [0, 1, 2, 3]

    async def test_missing_api_key_fails_clearly(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "google_maps_api_key", "")

        with pytest.raises(RoutesApiRoutingError, match="GOOGLE_MAPS_API_KEY"):
            await _algorithm()._request_order(
                [FakeLocation(), FakeLocation()],  # type: ignore[list-item]
                43.4,
                -80.5,
                True,
            )


class TestBillingShape:
    """Why this tier is cheaper than Fleet Routing, encoded as a test."""

    async def test_costs_one_request_per_driver_not_per_stop(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """computeRoutes bills per request, so 75 stops over 12 drivers is 12."""
        algorithm = _algorithm()
        locations = [FakeLocation(address=str(i)) for i in range(75)]
        requests = 0

        async def fake_cluster(**kwargs: Any) -> list[list[Any]]:
            locs = kwargs["locations"]
            size = len(locs) // 12
            return [locs[i * size : (i + 1) * size] for i in range(12)]

        async def fake_order(cluster: list[Any], *_args: Any) -> list[int]:
            nonlocal requests
            requests += 1
            return list(range(len(cluster)))

        monkeypatch.setattr(
            algorithm.clustering_algorithm, "cluster_locations", fake_cluster
        )
        monkeypatch.setattr(algorithm, "_request_order", fake_order)

        await algorithm.generate_routes(
            locations,  # type: ignore[arg-type]
            43.4,
            -80.5,
            _settings(num_routes=12),
        )

        assert requests == 12


class TestLogger:
    """The module logger is used for the unusable-response warning."""

    async def test_module_exposes_a_logger(self) -> None:
        from app.services.implementations import routes_api_routing_service

        assert isinstance(routes_api_routing_service.logger, logging.Logger)

"""Tests for the Routes API single-vehicle ordering tier.

Ordering is the cheap half of route generation: our clustering already decided
who goes where, so the failure that matters here is losing or duplicating a
stop while reordering, which would silently drop a delivery.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.config import settings
from app.schemas.route_generation import RouteGenerationSettings
from app.services.implementations.quota_service import PartiallyBilledError
from app.services.implementations.routes_api_routing_service import (
    MAX_INTERMEDIATES,
    RoutesApiRequestNotSentError,
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


class TestTierTimeout:
    """A hanging Google call must stop at this tier, not at the job."""

    async def test_slow_ordering_raises_timeout_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The cascade falls back on TimeoutError; anything else fails the job."""
        algorithm = _algorithm()
        locations = [FakeLocation(address=str(i)) for i in range(4)]
        cancelled = False

        async def fake_cluster(**kwargs: Any) -> list[list[Any]]:
            return [kwargs["locations"]]

        async def hanging_order(*_args: Any, **_kwargs: Any) -> list[int]:
            nonlocal cancelled
            try:
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                cancelled = True
                raise
            return [0, 1, 2, 3]

        monkeypatch.setattr(
            algorithm.clustering_algorithm, "cluster_locations", fake_cluster
        )
        monkeypatch.setattr(algorithm, "_request_order", hanging_order)

        with pytest.raises(TimeoutError):
            await algorithm.generate_routes(
                locations,  # type: ignore[arg-type]
                43.4,
                -80.5,
                _settings(num_routes=1),
                timeout_seconds=0.05,
            )

        # The in-flight request is dropped rather than left running behind the
        # job that gave up on it.
        assert cancelled

    async def test_a_budget_spent_by_clustering_leaves_none_for_ordering(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Remaining time is clamped at zero, not read as 'no timeout'."""
        algorithm = _algorithm()

        async def slow_cluster(**kwargs: Any) -> list[list[Any]]:
            await asyncio.sleep(0.05)
            return [kwargs["locations"]]

        async def hanging_order(*_args: Any, **_kwargs: Any) -> list[int]:
            await asyncio.sleep(30)
            return [0, 1]

        monkeypatch.setattr(
            algorithm.clustering_algorithm, "cluster_locations", slow_cluster
        )
        monkeypatch.setattr(algorithm, "_request_order", hanging_order)

        with pytest.raises(TimeoutError):
            await algorithm.generate_routes(
                [FakeLocation(), FakeLocation()],  # type: ignore[list-item]
                43.4,
                -80.5,
                _settings(num_routes=1),
                timeout_seconds=0.01,
            )

    async def test_no_timeout_means_no_deadline(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        algorithm = _algorithm()

        async def fake_cluster(**kwargs: Any) -> list[list[Any]]:
            return [kwargs["locations"]]

        async def fake_order(cluster: list[Any], *_args: Any) -> list[int]:
            return list(reversed(range(len(cluster))))

        monkeypatch.setattr(
            algorithm.clustering_algorithm, "cluster_locations", fake_cluster
        )
        monkeypatch.setattr(algorithm, "_request_order", fake_order)

        routes = await algorithm.generate_routes(
            [FakeLocation(address="a"), FakeLocation(address="b")],  # type: ignore[list-item]
            43.4,
            -80.5,
            _settings(num_routes=1),
        )

        assert [loc.address for loc in routes[0]] == ["b", "a"]


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


class TestPartialFailure:
    """One failed cluster must not hide the siblings Google already billed."""

    @staticmethod
    def _three_clusters(
        monkeypatch: pytest.MonkeyPatch,
        algorithm: RoutesApiSingleVehicleAlgorithm,
        sizes: tuple[int, int, int] = (3, 3, 3),
    ) -> list[Any]:
        locations = [FakeLocation(address=str(i)) for i in range(sum(sizes))]

        async def fake_cluster(**kwargs: Any) -> list[list[Any]]:
            locs = kwargs["locations"]
            a, b, _ = sizes
            return [locs[:a], locs[a : a + b], locs[a + b :]]

        monkeypatch.setattr(
            algorithm.clustering_algorithm, "cluster_locations", fake_cluster
        )
        return locations

    async def test_counts_every_request_google_answered(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Including the one it answered with an error: that request reached
        Google, and overcounting is the safe direction."""
        algorithm = _algorithm()
        locations = self._three_clusters(monkeypatch, algorithm)

        async def fake_order(cluster: list[Any], *_args: Any) -> list[int]:
            if cluster[0].address == "6":
                raise RoutesApiRoutingError("Routes API ordering failed: upstream.")
            return list(range(len(cluster)))

        monkeypatch.setattr(algorithm, "_request_order", fake_order)

        with pytest.raises(PartiallyBilledError) as caught:
            await algorithm.generate_routes(
                locations,
                43.4,
                -80.5,
                _settings(num_routes=3),
            )

        assert caught.value.units_billed == 3

    async def test_a_request_that_was_never_sent_is_not_billed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        algorithm = _algorithm()
        locations = self._three_clusters(monkeypatch, algorithm)

        async def fake_order(cluster: list[Any], *_args: Any) -> list[int]:
            if cluster[0].address == "6":
                raise RoutesApiRequestNotSentError("rejected before sending")
            return list(range(len(cluster)))

        monkeypatch.setattr(algorithm, "_request_order", fake_order)

        with pytest.raises(PartiallyBilledError) as caught:
            await algorithm.generate_routes(
                locations,
                43.4,
                -80.5,
                _settings(num_routes=3),
            )

        assert caught.value.units_billed == 2

    async def test_a_single_stop_cluster_is_never_billed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """It skips the call, so it must not be counted when a sibling fails."""
        algorithm = _algorithm()
        locations = self._three_clusters(monkeypatch, algorithm, sizes=(1, 3, 3))

        async def fake_order(cluster: list[Any], *_args: Any) -> list[int]:
            if cluster[0].address == "4":
                raise RoutesApiRoutingError("Routes API ordering failed: upstream.")
            return list(range(len(cluster)))

        monkeypatch.setattr(algorithm, "_request_order", fake_order)

        with pytest.raises(PartiallyBilledError) as caught:
            await algorithm.generate_routes(
                locations,
                43.4,
                -80.5,
                _settings(num_routes=3),
            )

        assert caught.value.units_billed == 2

    async def test_a_missing_api_key_bills_nothing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A misconfigured tier must hand back its whole reservation, or it
        burns the allowance failing on every run."""
        monkeypatch.setattr(settings, "google_maps_api_key", "")
        algorithm = _algorithm()
        locations = self._three_clusters(monkeypatch, algorithm)

        with pytest.raises(PartiallyBilledError) as caught:
            await algorithm.generate_routes(
                locations,
                43.4,
                -80.5,
                _settings(num_routes=3),
            )

        assert caught.value.units_billed == 0


class TestLogger:
    """The module logger is used for the unusable-response warning."""

    async def test_module_exposes_a_logger(self) -> None:
        from app.services.implementations import routes_api_routing_service

        assert isinstance(routes_api_routing_service.logger, logging.Logger)

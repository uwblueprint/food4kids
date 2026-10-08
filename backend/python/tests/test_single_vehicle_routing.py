"""Tests for the single-vehicle middle rung of the generation cascade."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import pytest

from app.schemas.route_generation import RouteGenerationSettings
from app.services.implementations.single_vehicle_routing import (
    SingleVehicleRoutingAlgorithm,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

pytestmark = pytest.mark.asyncio


@dataclass
class FakeLocation:
    """Lightweight stand-in for Location that avoids SQLAlchemy mapper init."""

    address: str = "123 Test St"
    location_id: UUID = field(default_factory=uuid4)


def _settings(num_routes: int = 3) -> RouteGenerationSettings:
    return RouteGenerationSettings(
        route_start_time=datetime(2026, 7, 7, 9, 0),
        num_routes=num_routes,
        return_to_warehouse=False,
        max_boxes_per_driver=10,
        children_per_box=2,
        service_time_minutes=3,
    )


def _stops(*names: str) -> list[Any]:
    return [FakeLocation(address=name) for name in names]


def _addresses(routes: list[list[Any]]) -> list[list[str]]:
    return [[stop.address for stop in route] for route in routes]


class Harness:
    """The algorithm with clustering and Route Optimization stubbed out."""

    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        clusters: list[list[Any]],
        order: Callable[[list[Any]], Awaitable[list[list[Any]]]] | None = None,
        cluster_delay: float = 0.0,
    ) -> None:
        self.algorithm = SingleVehicleRoutingAlgorithm()
        self.requests: list[tuple[list[str], RouteGenerationSettings]] = []

        async def fake_cluster(*_args: Any, **_kwargs: Any) -> list[list[Any]]:
            await asyncio.sleep(cluster_delay)
            return clusters

        async def fake_optimize(
            cluster: list[Any], _lat: float, _lon: float, settings: Any
        ) -> list[list[Any]]:
            self.requests.append(([s.address for s in cluster], settings))
            if order is None:
                return [list(reversed(cluster))]
            return await order(cluster)

        monkeypatch.setattr(self.algorithm.clustering, "generate_routes", fake_cluster)
        monkeypatch.setattr(self.algorithm.optimizer, "generate_routes", fake_optimize)

    async def run(
        self, settings: RouteGenerationSettings | None = None, **kwargs: Any
    ) -> list[list[Any]]:
        # The stubbed clustering ignores its input and returns the clusters.
        return await self.algorithm.generate_routes(
            _stops("placeholder"),
            43.4,
            -80.5,
            settings or _settings(),
            **kwargs,
        )


class TestOrdering:
    async def test_each_cluster_comes_back_in_googles_order(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        harness = Harness(monkeypatch, [_stops("a", "b", "c"), _stops("d", "e")])

        routes = await harness.run()

        assert _addresses(routes) == [["c", "b", "a"], ["e", "d"]]

    async def test_each_request_carries_one_vehicle_and_nothing_else_changed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """One vehicle is what bills the request to the cheaper SKU."""
        harness = Harness(monkeypatch, [_stops("a", "b"), _stops("c", "d")])
        settings = _settings(num_routes=2)

        await harness.run(settings)

        assert len(harness.requests) == 2
        for _cluster, sent in harness.requests:
            assert sent.num_routes == 1
            assert sent.model_dump(exclude={"num_routes"}) == settings.model_dump(
                exclude={"num_routes"}
            )

    @pytest.mark.parametrize("size", [0, 1])
    async def test_a_cluster_too_small_to_order_sends_no_request(
        self, monkeypatch: pytest.MonkeyPatch, size: int
    ) -> None:
        small = _stops(*"x" * size)
        harness = Harness(monkeypatch, [small, _stops("a", "b")])

        routes = await harness.run()

        assert [cluster for cluster, _ in harness.requests] == [["a", "b"]]
        assert _addresses(routes) == [["x"] * size, ["b", "a"]]

    async def test_no_locations_makes_no_calls(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        harness = Harness(monkeypatch, [_stops("a", "b")])

        routes = await harness.algorithm.generate_routes([], 43.4, -80.5, _settings())

        assert routes == []
        assert harness.requests == []


class TestUnusableResponse:
    """A route that loses or invents a stop must never be saved."""

    @pytest.mark.parametrize(
        "mangle",
        [
            pytest.param(lambda c: c[:-1], id="drops a stop"),
            pytest.param(lambda c: [*c, c[0]], id="duplicates a stop"),
            pytest.param(lambda c: [*c[:-1], FakeLocation()], id="swaps a stop"),
        ],
    )
    async def test_raises_rather_than_returning_a_wrong_route(
        self, monkeypatch: pytest.MonkeyPatch, mangle: Any
    ) -> None:
        async def bad_order(cluster: list[Any]) -> list[list[Any]]:
            return [mangle(cluster)]

        harness = Harness(monkeypatch, [_stops("a", "b", "c")], order=bad_order)

        with pytest.raises(RuntimeError, match="of a cluster's 3 stops"):
            await harness.run()

    async def test_an_optimizer_error_propagates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The cascade decides what a failure means; this tier just reports it."""

        async def failing(_cluster: list[Any]) -> list[list[Any]]:
            raise RuntimeError("upstream 500")

        harness = Harness(monkeypatch, [_stops("a", "b")], order=failing)

        with pytest.raises(RuntimeError, match="upstream 500"):
            await harness.run()


class TestTierTimeout:
    """A hanging request must stop at this tier, not at the job."""

    async def test_slow_ordering_raises_timeout_error_and_cancels(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cancelled = False

        async def hanging(cluster: list[Any]) -> list[list[Any]]:
            nonlocal cancelled
            try:
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                cancelled = True
                raise
            return [cluster]

        harness = Harness(monkeypatch, [_stops("a", "b")], order=hanging)

        with pytest.raises(TimeoutError):
            await harness.run(timeout_seconds=0.05)
        assert cancelled

    async def test_time_spent_clustering_comes_out_of_the_budget(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Remaining time is clamped at zero, not read as 'no timeout'."""

        async def slow(cluster: list[Any]) -> list[list[Any]]:
            await asyncio.sleep(30)
            return [cluster]

        harness = Harness(
            monkeypatch, [_stops("a", "b")], order=slow, cluster_delay=0.05
        )

        with pytest.raises(TimeoutError):
            await harness.run(timeout_seconds=0.01)

    async def test_no_timeout_means_no_deadline(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def a_little_slow(cluster: list[Any]) -> list[list[Any]]:
            await asyncio.sleep(0.05)
            return [cluster]

        harness = Harness(monkeypatch, [_stops("a", "b")], order=a_little_slow)

        assert _addresses(await harness.run()) == [["a", "b"]]

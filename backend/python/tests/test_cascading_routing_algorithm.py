"""Tests for the budget-aware route generation cascade.

The cases that matter are the transitions: when a paid tier is approved,
refused, or fails, and what generation falls back to each time.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.dependencies.services import get_routing_algorithm
from app.schemas.route_generation import RouteGenerationSettings
from app.services.implementations.cascading_routing_algorithm import (
    FLEET_ROUTING_USD_PER_SHIPMENT,
    SINGLE_VEHICLE_USD_PER_SHIPMENT,
    CascadingRoutingAlgorithm,
    Tier,
    cluster_sweep_tier,
    fleet_routing_tier,
    single_vehicle_tier,
)
from app.services.implementations.google_maps_routing_service import (
    GoogleMapsFleetRoutingAlgorithm,
)
from app.services.implementations.single_vehicle_routing import (
    SingleVehicleRoutingAlgorithm,
)
from app.services.implementations.sweep_clustering import SweepRoutingAlgorithm

pytestmark = pytest.mark.asyncio


@dataclass
class FakeLocation:
    """Lightweight stand-in for Location that avoids SQLAlchemy mapper init."""

    location_id: UUID = field(default_factory=uuid4)


class FakeAlgorithm:
    """Routing algorithm that records its calls, or fails on demand."""

    def __init__(self, error: BaseException | None = None) -> None:
        self.error = error
        self.calls = 0
        self.timeouts: list[float | None] = []

    async def generate_routes(
        self,
        locations: list[Any],
        _warehouse_lat: float,
        _warehouse_lon: float,
        _settings: Any,
        timeout_seconds: float | None = None,
    ) -> list[list[Any]]:
        self.calls += 1
        self.timeouts.append(timeout_seconds)
        if self.error is not None:
            raise self.error
        return [list(locations)]


class FakeSpend:
    """Approves tiers by name and records every charge it is asked for."""

    def __init__(
        self, approve: set[str] | None = None, error: Exception | None = None
    ) -> None:
        self.approve = approve or set()
        self.error = error
        self.checked: list[tuple[str, int, float]] = []
        self.charged: list[tuple[str, int, float]] = []

    async def try_charge(self, tier: str, shipments: int, cost_usd: float) -> bool:
        self.checked.append((tier, shipments, cost_usd))
        if self.error is not None:
            raise self.error
        if tier in self.approve:
            self.charged.append((tier, shipments, cost_usd))
            return True
        return False


@pytest.fixture
def gen_settings() -> RouteGenerationSettings:
    return RouteGenerationSettings(
        route_start_time=datetime(2026, 8, 21, 8, 0),
        num_routes=4,
        max_boxes_per_driver=10,
        children_per_box=2,
        service_time_minutes=3,
    )


@pytest.fixture
def locations() -> list[Any]:
    return [FakeLocation() for _ in range(9)]


def _paid(name: str, algorithm: FakeAlgorithm) -> Tier:
    return Tier(
        name=name,
        algorithm=algorithm,
        usd_per_shipment=0.01,
    )


class Ladder:
    """Fleet, single-vehicle and free tiers over fake engines."""

    def __init__(self, spend: FakeSpend, **errors: BaseException) -> None:
        self.fleet = FakeAlgorithm(errors.get("fleet"))
        self.single = FakeAlgorithm(errors.get("single"))
        self.free = FakeAlgorithm(errors.get("free"))
        self.cascade = CascadingRoutingAlgorithm(
            spend,  # type: ignore[arg-type]
            [
                _paid("fleet_routing", self.fleet),
                _paid("single_vehicle", self.single),
                Tier(name="cluster_sweep", algorithm=self.free),
            ],
        )

    @property
    def calls(self) -> tuple[int, int, int]:
        return (self.fleet.calls, self.single.calls, self.free.calls)

    async def run(
        self, locations: list[Any], settings: Any, **kwargs: Any
    ) -> list[list[Any]]:
        return await self.cascade.generate_routes(
            locations, 43.0, -79.0, settings, **kwargs
        )


class TestQualityOrder:
    @pytest.mark.parametrize(
        ("approved", "calls"),
        [
            ({"fleet_routing", "single_vehicle"}, (1, 0, 0)),
            ({"fleet_routing"}, (1, 0, 0)),
            ({"single_vehicle"}, (0, 1, 0)),
            (set(), (0, 0, 1)),
        ],
    )
    async def test_runs_the_best_tier_the_budget_approves(
        self,
        locations: list[Any],
        gen_settings: Any,
        approved: set[str],
        calls: tuple[int, int, int],
    ) -> None:
        ladder = Ladder(FakeSpend(approve=approved))

        assert await ladder.run(locations, gen_settings) == [locations]
        assert ladder.calls == calls

    async def test_stops_asking_once_a_tier_is_approved(
        self, locations: list[Any], gen_settings: Any
    ) -> None:
        """Asking about a lower tier would record a charge nobody makes."""
        spend = FakeSpend(approve={"fleet_routing", "single_vehicle"})

        await Ladder(spend).run(locations, gen_settings)

        assert [tier for tier, _, _ in spend.checked] == ["fleet_routing"]

    async def test_the_free_tier_is_never_checked(
        self, locations: list[Any], gen_settings: Any
    ) -> None:
        spend = FakeSpend()

        await Ladder(spend).run(locations, gen_settings)

        assert [tier for tier, _, _ in spend.checked] == [
            "fleet_routing",
            "single_vehicle",
        ]

    async def test_charge_is_shipments_times_price(
        self, locations: list[Any], gen_settings: Any
    ) -> None:
        spend = FakeSpend(approve={"fleet_routing"})

        await Ladder(spend).run(locations, gen_settings)

        # 9 locations + 4 forced pickups, at the fake tier's $0.01.
        ((tier, shipments, cost),) = spend.charged
        assert (tier, shipments) == ("fleet_routing", 13)
        assert cost == pytest.approx(0.13)

    async def test_passes_the_timeout_to_the_tier(
        self, locations: list[Any], gen_settings: Any
    ) -> None:
        ladder = Ladder(FakeSpend(approve={"fleet_routing"}))

        await ladder.run(locations, gen_settings, timeout_seconds=12.5)

        assert ladder.fleet.timeouts == [12.5]


class TestFallback:
    @pytest.mark.parametrize(
        "error",
        [
            pytest.param(TimeoutError(), id="timeout"),
            pytest.param(RuntimeError("upstream 500"), id="api error"),
            pytest.param(ValueError("bad payload"), id="rejected request"),
        ],
    )
    async def test_a_failed_tier_falls_to_the_next_and_keeps_its_charge(
        self, locations: list[Any], gen_settings: Any, error: Exception
    ) -> None:
        """The request may have been billed, so its charge is never undone."""
        spend = FakeSpend(approve={"fleet_routing", "single_vehicle"})
        ladder = Ladder(spend, fleet=error)

        assert await ladder.run(locations, gen_settings) == [locations]
        assert ladder.calls == (1, 1, 0)
        assert [tier for tier, _, _ in spend.charged] == [
            "fleet_routing",
            "single_vehicle",
        ]

    async def test_a_failed_spend_check_skips_the_tier_not_the_job(
        self, locations: list[Any], gen_settings: Any
    ) -> None:
        ladder = Ladder(FakeSpend(error=ConnectionError("pool exhausted")))

        assert await ladder.run(locations, gen_settings) == [locations]
        assert ladder.calls == (0, 0, 1)

    async def test_cancellation_is_not_treated_as_a_failure(
        self, locations: list[Any], gen_settings: Any
    ) -> None:
        """The job-level timeout cancels; falling back would outlive it."""
        ladder = Ladder(
            FakeSpend(approve={"fleet_routing"}), fleet=asyncio.CancelledError()
        )

        with pytest.raises(asyncio.CancelledError):
            await ladder.run(locations, gen_settings)
        assert ladder.calls == (1, 0, 0)

    async def test_names_every_attempt_when_nothing_can_run(
        self, locations: list[Any], gen_settings: Any
    ) -> None:
        ladder = Ladder(
            FakeSpend(approve={"single_vehicle"}),
            single=RuntimeError("upstream 500"),
            free=ValueError("not enough drivers"),
        )

        with pytest.raises(RuntimeError) as raised:
            await ladder.run(locations, gen_settings)

        message = str(raised.value)
        assert "fleet_routing (over budget)" in message
        assert "single_vehicle (failed: RuntimeError('upstream 500'))" in message
        assert "cluster_sweep (failed: ValueError('not enough drivers'))" in message


class TestShippedTiers:
    """The real tiers bill what their engines send, at Google's list price."""

    async def test_engines_and_order(self) -> None:
        tiers = [fleet_routing_tier(), single_vehicle_tier(), cluster_sweep_tier()]

        assert [type(t.algorithm) for t in tiers] == [
            GoogleMapsFleetRoutingAlgorithm,
            SingleVehicleRoutingAlgorithm,
            SweepRoutingAlgorithm,
        ]
        assert tiers[2].usd_per_shipment is None

    @pytest.mark.parametrize(
        ("tier", "per_shipment"),
        [
            (fleet_routing_tier, FLEET_ROUTING_USD_PER_SHIPMENT),
            (single_vehicle_tier, SINGLE_VEHICLE_USD_PER_SHIPMENT),
        ],
    )
    async def test_pricing(self, tier: Any, per_shipment: float) -> None:
        assert tier().usd_per_shipment == per_shipment


async def test_the_shipped_algorithm_is_the_full_ladder() -> None:
    algorithm = get_routing_algorithm(session_maker=None)  # type: ignore[arg-type]

    assert isinstance(algorithm, CascadingRoutingAlgorithm)
    assert [tier.name for tier in algorithm.tiers] == [
        "fleet_routing",
        "single_vehicle",
        "cluster_sweep",
    ]

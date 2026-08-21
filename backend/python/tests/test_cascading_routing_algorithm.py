"""Tests for the tiered route generation cascade.

The cascade decides how much we pay for routes and how good they are, so the
cases that matter are the transitions: when a tier is skipped, when its quota
is handed back, and when it is deliberately kept.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.models.api_usage import ApiSku
from app.schemas.route_generation import RouteGenerationSettings
from app.services.implementations.cascading_routing_algorithm import (
    CascadingRoutingAlgorithm,
    Tier,
    routes_compute_units,
)
from app.services.implementations.quota_service import (
    QuotaService,
    fleet_routing_units,
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


class FakeAlgorithm:
    """Routing algorithm that records its calls, or fails on demand."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls = 0

    async def generate_routes(
        self,
        locations: list[Any],
        _warehouse_lat: float,
        _warehouse_lon: float,
        _settings: Any,
        timeout_seconds: float | None = None,  # noqa: ARG002
    ) -> list[list[Any]]:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return [list(locations)]


@pytest.fixture
def gen_settings() -> RouteGenerationSettings:
    return RouteGenerationSettings(
        route_start_time=datetime(2026, 8, 21, 8, 0), num_routes=4
    )


@pytest.fixture
def locations() -> list[Any]:
    return [FakeLocation() for _ in range(9)]


@pytest_asyncio.fixture
async def maker(test_db_engine: Any) -> Any:
    """Session factory plus cleanup — the cascade commits outside the test's
    rolled-back session, deliberately, so rows have to be removed by hand."""
    factory = async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    yield factory
    async with factory() as session:
        await session.execute(text("DELETE FROM api_usage"))
        await session.commit()


def _quota(**budgets: int) -> QuotaService:
    return QuotaService(
        logging.getLogger(__name__),
        Settings(
            quota_fleet_routing_shipments=budgets.get("fleet", 1000),
            quota_routes_compute_requests=budgets.get("routes", 10000),
        ),
    )


def _cascade(
    quota: QuotaService,
    maker: Any,
    paid: FakeAlgorithm,
    free: FakeAlgorithm,
) -> CascadingRoutingAlgorithm:
    return CascadingRoutingAlgorithm(
        logging.getLogger(__name__),
        quota,
        maker,
        [
            Tier(
                name="fleet_routing",
                algorithm=paid,
                sku=ApiSku.FLEET_ROUTING,
                units_for=fleet_routing_units,
            ),
            Tier(name="cluster_sweep", algorithm=free),
        ],
    )


class TestQualityOrder:
    """The best tier runs whenever its free allowance can cover the job."""

    async def test_uses_the_top_tier_when_quota_allows(
        self, maker: Any, locations: list[Any], gen_settings: Any
    ) -> None:
        paid, free = FakeAlgorithm(), FakeAlgorithm()
        cascade = _cascade(_quota(fleet=1000), maker, paid, free)

        await cascade.generate_routes(locations, 43.0, -79.0, gen_settings)

        assert paid.calls == 1
        assert free.calls == 0
        assert cascade.last_tier_used == "fleet_routing"

    async def test_consumes_shipments_including_the_per_vehicle_pickups(
        self, maker: Any, locations: list[Any], gen_settings: Any
    ) -> None:
        quota = _quota(fleet=1000)
        cascade = _cascade(quota, maker, FakeAlgorithm(), FakeAlgorithm())

        await cascade.generate_routes(locations, 43.0, -79.0, gen_settings)

        async with maker() as session:
            used = await quota.units_used(session, ApiSku.FLEET_ROUTING)
        assert used == 9 + 4


class TestFallback:
    """Exhausting a tier's free room drops to the next, never to an error."""

    async def test_falls_back_when_the_top_tier_has_no_free_room(
        self, maker: Any, locations: list[Any], gen_settings: Any
    ) -> None:
        paid, free = FakeAlgorithm(), FakeAlgorithm()
        # Room for 12 shipments; this job needs 13.
        cascade = _cascade(_quota(fleet=12), maker, paid, free)

        await cascade.generate_routes(locations, 43.0, -79.0, gen_settings)

        assert paid.calls == 0
        assert free.calls == 1
        assert cascade.last_tier_used == "cluster_sweep"

    async def test_the_free_floor_needs_no_quota(
        self, maker: Any, locations: list[Any], gen_settings: Any
    ) -> None:
        """cluster+sweep is in-house, so it runs with every budget at zero."""
        free = FakeAlgorithm()
        cascade = _cascade(_quota(fleet=0), maker, FakeAlgorithm(), free)

        routes = await cascade.generate_routes(locations, 43.0, -79.0, gen_settings)

        assert free.calls == 1
        assert routes == [locations]

    async def test_raises_when_no_tier_can_run(
        self, maker: Any, locations: list[Any], gen_settings: Any
    ) -> None:
        """Only reachable if the free floor was left out of the cascade."""
        cascade = CascadingRoutingAlgorithm(
            logging.getLogger(__name__),
            _quota(fleet=0),
            maker,
            [
                Tier(
                    name="fleet_routing",
                    algorithm=FakeAlgorithm(),
                    sku=ApiSku.FLEET_ROUTING,
                    units_for=fleet_routing_units,
                )
            ],
        )

        with pytest.raises(RuntimeError, match="No routing tier"):
            await cascade.generate_routes(locations, 43.0, -79.0, gen_settings)


class TestFailureHandling:
    """A tier that breaks must not quietly eat a month of quota."""

    async def test_a_failing_tier_hands_its_quota_back(
        self, maker: Any, locations: list[Any], gen_settings: Any
    ) -> None:
        """Otherwise a misconfigured tier burns the allowance failing."""
        quota = _quota(fleet=1000)
        paid = FakeAlgorithm(error=ValueError("bad credentials"))
        free = FakeAlgorithm()
        cascade = _cascade(quota, maker, paid, free)

        await cascade.generate_routes(locations, 43.0, -79.0, gen_settings)

        async with maker() as session:
            assert await quota.units_used(session, ApiSku.FLEET_ROUTING) == 0
        assert free.calls == 1

    async def test_a_timeout_keeps_its_reservation(
        self, maker: Any, locations: list[Any], gen_settings: Any
    ) -> None:
        """A timed-out request may still have reached Google and been billed.

        Overcounting costs a slightly worse route; undercounting costs money.
        """
        quota = _quota(fleet=1000)
        paid = FakeAlgorithm(error=TimeoutError())
        free = FakeAlgorithm()
        cascade = _cascade(quota, maker, paid, free)

        await cascade.generate_routes(locations, 43.0, -79.0, gen_settings)

        async with maker() as session:
            assert await quota.units_used(session, ApiSku.FLEET_ROUTING) == 13
        assert free.calls == 1

    async def test_generation_still_succeeds_when_the_paid_tier_breaks(
        self, maker: Any, locations: list[Any], gen_settings: Any
    ) -> None:
        cascade = _cascade(
            _quota(fleet=1000),
            maker,
            FakeAlgorithm(error=RuntimeError("upstream 500")),
            FakeAlgorithm(),
        )

        routes = await cascade.generate_routes(locations, 43.0, -79.0, gen_settings)

        assert routes == [locations]
        assert cascade.last_tier_used == "cluster_sweep"


class TestUsageIsIndependentOfTheJob:
    """Google bills for the call however the job ends."""

    async def test_reservation_survives_a_rolled_back_job(
        self, maker: Any, locations: list[Any], gen_settings: Any
    ) -> None:
        """The cascade commits quota on its own session, not the job's."""
        quota = _quota(fleet=1000)
        cascade = _cascade(quota, maker, FakeAlgorithm(), FakeAlgorithm())

        await cascade.generate_routes(locations, 43.0, -79.0, gen_settings)

        async with maker() as fresh:
            assert await quota.units_used(fresh, ApiSku.FLEET_ROUTING) == 13


class TestBillingUnitsPerTier:
    """Units are not comparable across SKUs."""

    async def test_routes_compute_counts_requests_not_shipments(self) -> None:
        """One computeRoutes call per vehicle, regardless of stop count."""
        assert routes_compute_units(75, 12) == 12
        assert fleet_routing_units(75, 12) == 87

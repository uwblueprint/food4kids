"""Tests for per-SKU quota tracking.

The counter decides whether route generation calls a paid API, so the two
failures that matter are opposite: undercounting sails past the free allowance
and costs money, overcounting downgrades route quality for no reason.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.models.api_usage import ApiSku
from app.schemas.route_generation import RouteGenerationSettings
from app.services.implementations.google_maps_routing_service import (
    GoogleMapsFleetRoutingAlgorithm,
)
from app.services.implementations.quota_service import (
    SKU_UNITS,
    QuotaService,
    fleet_routing_units,
)

pytestmark = pytest.mark.asyncio

MONTH = "202608"


@dataclass
class FakeLocation:
    """Lightweight stand-in for Location that avoids SQLAlchemy mapper init."""

    latitude: float = 43.0
    longitude: float = -79.0
    address: str = "123 Test St"
    location_id: UUID = field(default_factory=uuid4)
    num_children: int = 2


def _service(**budgets: int) -> QuotaService:
    settings = Settings(
        quota_fleet_routing_shipments=budgets.get("fleet", 1000),
        quota_single_vehicle_shipments=budgets.get("single", 1000),
        quota_routes_compute_requests=budgets.get("routes", 10000),
    )
    return QuotaService(logging.getLogger(__name__), settings)


class TestBillingUnits:
    """Shipments billed per run must match what the payload actually sends."""

    async def test_counts_one_shipment_per_delivery_and_per_vehicle(self) -> None:
        assert fleet_routing_units(num_locations=75, num_vehicles=12) == 87

    async def test_matches_the_real_payload_builder(self) -> None:
        """Pins the estimate to ``_build_payload``.

        The payload adds a forced pickup per vehicle on top of the deliveries.
        If that changes, the quota estimate silently undercounts every run —
        so this fails loudly instead.
        """
        algorithm = GoogleMapsFleetRoutingAlgorithm()
        locations = [FakeLocation() for _ in range(9)]
        settings = RouteGenerationSettings(
            route_start_time=datetime(2026, 8, 21, 8, 0), num_routes=4
        )

        payload = algorithm._build_payload(
            locations,  # type: ignore[arg-type]
            warehouse_lat=43.0,
            warehouse_lon=-79.0,
            settings=settings,
        )
        actual_shipments = len(payload["model"]["shipments"])

        assert actual_shipments == fleet_routing_units(num_locations=9, num_vehicles=4)

    async def test_every_sku_declares_its_unit(self) -> None:
        """A bare count is ambiguous — shipments and requests are not alike."""
        assert {sku.value for sku in ApiSku} == set(SKU_UNITS)


class TestTryReserve:
    """Reservation is the gate that keeps generation inside the free tier."""

    async def test_reserves_when_there_is_room(
        self, test_session: AsyncSession
    ) -> None:
        service = _service(fleet=100)

        assert await service.try_reserve(test_session, ApiSku.FLEET_ROUTING, 87, MONTH)
        assert await service.units_used(test_session, ApiSku.FLEET_ROUTING, MONTH) == 87

    async def test_refuses_when_the_request_would_exceed_the_budget(
        self, test_session: AsyncSession
    ) -> None:
        service = _service(fleet=100)
        await service.try_reserve(test_session, ApiSku.FLEET_ROUTING, 87, MONTH)

        assert not await service.try_reserve(
            test_session, ApiSku.FLEET_ROUTING, 87, MONTH
        )

    async def test_a_refused_reservation_consumes_nothing(
        self, test_session: AsyncSession
    ) -> None:
        """A partial claim would strand quota nobody can use."""
        service = _service(fleet=100)
        await service.try_reserve(test_session, ApiSku.FLEET_ROUTING, 87, MONTH)

        await service.try_reserve(test_session, ApiSku.FLEET_ROUTING, 87, MONTH)

        assert await service.units_used(test_session, ApiSku.FLEET_ROUTING, MONTH) == 87

    async def test_a_request_landing_exactly_on_the_budget_fits(
        self, test_session: AsyncSession
    ) -> None:
        service = _service(fleet=100)

        assert await service.try_reserve(test_session, ApiSku.FLEET_ROUTING, 100, MONTH)

    async def test_one_unit_over_does_not(self, test_session: AsyncSession) -> None:
        service = _service(fleet=100)

        assert not await service.try_reserve(
            test_session, ApiSku.FLEET_ROUTING, 101, MONTH
        )

    async def test_skus_draw_on_separate_allowances(
        self, test_session: AsyncSession
    ) -> None:
        """Google grants these per SKU; spending one must not touch another."""
        service = _service(fleet=100, routes=100)
        await service.try_reserve(test_session, ApiSku.FLEET_ROUTING, 100, MONTH)

        assert await service.try_reserve(
            test_session, ApiSku.ROUTES_COMPUTE, 100, MONTH
        )

    async def test_a_new_month_starts_from_zero(
        self, test_session: AsyncSession
    ) -> None:
        service = _service(fleet=100)
        await service.try_reserve(test_session, ApiSku.FLEET_ROUTING, 100, "202608")

        assert await service.try_reserve(
            test_session, ApiSku.FLEET_ROUTING, 100, "202609"
        )

    async def test_zero_units_is_a_no_op(self, test_session: AsyncSession) -> None:
        service = _service(fleet=0)

        assert await service.try_reserve(test_session, ApiSku.FLEET_ROUTING, 0, MONTH)

    async def test_a_zero_budget_refuses_everything(
        self, test_session: AsyncSession
    ) -> None:
        """How an admin forces a tier off without code changes."""
        service = _service(fleet=0)

        assert not await service.try_reserve(
            test_session, ApiSku.FLEET_ROUTING, 1, MONTH
        )


class TestConcurrentReservation:
    """Two jobs starting together must not both claim the last of the quota."""

    async def test_concurrent_reservations_never_exceed_the_budget(
        self, test_db_engine: Any
    ) -> None:
        """The classic check-then-act race, on real Postgres.

        Ten jobs race for a budget that fits four. Separate sessions because a
        single one would serialize them and prove nothing.
        """
        budget, units, racers = 40, 10, 10
        service = _service(fleet=budget)
        maker = async_sessionmaker(
            test_db_engine, class_=AsyncSession, expire_on_commit=False
        )

        async def claim() -> bool:
            async with maker() as session:
                granted = await service.try_reserve(
                    session, ApiSku.FLEET_ROUTING, units, MONTH
                )
                await session.commit()
                return granted

        results = await asyncio.gather(*(claim() for _ in range(racers)))

        async with maker() as session:
            used = await service.units_used(session, ApiSku.FLEET_ROUTING, MONTH)
            # Committed rows escape the per-test rollback, so clean up by hand.
            await session.execute(
                text("DELETE FROM api_usage WHERE billing_month = :m"),
                {"m": MONTH},
            )
            await session.commit()

        assert sum(results) == budget // units
        assert used == budget


class TestRecord:
    """Ungated calls still have to show up in the counter."""

    async def test_records_past_the_budget(self, test_session: AsyncSession) -> None:
        """Polylines are issued while saving a generation, too late to refuse.

        The allowance is spent either way, so the counter must say so rather
        than quietly under-reporting.
        """
        service = _service(routes=10)

        await service.record(test_session, ApiSku.ROUTES_COMPUTE, 25, MONTH)

        assert (
            await service.units_used(test_session, ApiSku.ROUTES_COMPUTE, MONTH) == 25
        )

    async def test_accumulates(self, test_session: AsyncSession) -> None:
        service = _service()

        await service.record(test_session, ApiSku.ROUTES_COMPUTE, 12, MONTH)
        await service.record(test_session, ApiSku.ROUTES_COMPUTE, 12, MONTH)

        assert (
            await service.units_used(test_session, ApiSku.ROUTES_COMPUTE, MONTH) == 24
        )


class TestRelease:
    """Units handed back when a reserved call provably never happened."""

    async def test_returns_unused_units(self, test_session: AsyncSession) -> None:
        service = _service(fleet=100)
        await service.try_reserve(test_session, ApiSku.FLEET_ROUTING, 87, MONTH)

        await service.release(test_session, ApiSku.FLEET_ROUTING, 87, MONTH)

        assert await service.units_used(test_session, ApiSku.FLEET_ROUTING, MONTH) == 0

    async def test_cannot_drive_the_counter_negative(
        self, test_session: AsyncSession
    ) -> None:
        """A negative count would manufacture free quota out of nothing."""
        service = _service(fleet=100)
        await service.try_reserve(test_session, ApiSku.FLEET_ROUTING, 10, MONTH)

        await service.release(test_session, ApiSku.FLEET_ROUTING, 999, MONTH)

        assert await service.units_used(test_session, ApiSku.FLEET_ROUTING, MONTH) == 0

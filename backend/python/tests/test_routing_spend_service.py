"""Tests for the budget check that gates paid route generation.

Runs against real Postgres: the ledger query, the month floor and the
advisory lock are the parts most likely to be wrong.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import select

from app.models.routing_charge import RoutingCharge
from app.services.implementations.billing_service import BillingSummary
from app.services.implementations.routing_spend_service import (
    EXPORT_LAG,
    RoutingSpendService,
)
from app.utilities.billing_client import BillingError
from app.utilities.datetime_utils import now_local, now_utc

pytestmark = pytest.mark.asyncio


def _summary(**overrides: Any) -> BillingSummary:
    """A USD account with $20 of net spend against a $100 budget."""
    base = BillingSummary(
        project_id="f4k",
        invoice_month="2026-10",
        currency="USD",
        month_to_date_cost=20.0,
        gross_cost=20.0,
        credits=0.0,
        budget_amount=100.0,
        budget_currency="USD",
        budget_display_name="Monthly",
        budget_scope="project",
        usd_conversion_rate=1.0,
        data_as_of=now_utc(),
    )
    return replace(base, **overrides)


class FakeBilling:
    def __init__(self, summary: BillingSummary | None = None, error: Any = None):
        self.summary = summary or _summary()
        self.error = error

    async def get_month_to_date_summary(self) -> BillingSummary:
        if self.error is not None:
            raise self.error
        return self.summary


@pytest_asyncio.fixture
async def maker(test_db_engine: Any) -> Any:
    """The service commits on its own sessions, so rows are removed by hand."""
    factory = async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    yield factory
    async with factory() as session:
        await session.execute(text("DELETE FROM routing_charge"))
        await session.commit()


def _service(
    maker: Any, billing: FakeBilling | None = None, credit_usd: float = 0.0
) -> RoutingSpendService:
    return RoutingSpendService(
        logging.getLogger(__name__),
        billing or FakeBilling(),  # type: ignore[arg-type]
        maker,
        credit_usd,
    )


async def _charges(maker: Any) -> list[tuple[str, int, float]]:
    async with maker() as session:
        rows = (await session.execute(select(RoutingCharge))).scalars().all()
        return sorted((r.tier, r.shipments, r.estimated_cost_usd) for r in rows)


async def _add_charge(maker: Any, cost_usd: float, created_at: datetime) -> None:
    async with maker() as session:
        session.add(
            RoutingCharge(
                tier="fleet_routing",
                shipments=1,
                estimated_cost_usd=cost_usd,
                created_at=created_at,
            )
        )
        await session.commit()


class TestBudget:
    async def test_approves_and_records_a_charge_that_fits(self, maker: Any) -> None:
        approved = await _service(maker).try_charge("fleet_routing", 87, 2.61)

        assert approved
        assert await _charges(maker) == [("fleet_routing", 87, 2.61)]

    @pytest.mark.parametrize(
        ("cost", "approved"),
        [(79.99, True), (80.0, True), (80.01, False)],
    )
    async def test_the_budget_is_inclusive(
        self, maker: Any, cost: float, approved: bool
    ) -> None:
        """$20 spent of $100 leaves exactly $80."""
        assert await _service(maker).try_charge("t", 1, cost) is approved

    async def test_a_refused_charge_records_nothing(self, maker: Any) -> None:
        assert not await _service(maker).try_charge("fleet_routing", 1, 500.0)
        assert await _charges(maker) == []

    async def test_spend_already_over_budget_refuses_even_a_free_estimate(
        self, maker: Any
    ) -> None:
        billing = FakeBilling(_summary(month_to_date_cost=120.0))

        assert not await _service(maker, billing).try_charge("t", 0, 0.0)


class TestCredit:
    """Net spend already has used credit taken off; the rest absorbs new calls."""

    @pytest.mark.parametrize(("credit_usd", "approved"), [(0.0, False), (250.0, True)])
    async def test_unused_credit_covers_a_call_the_budget_alone_could_not(
        self, maker: Any, credit_usd: float, approved: bool
    ) -> None:
        """A summer run, 1,760 shipments at $0.03, with $5 of budget left."""
        billing = FakeBilling(_summary(month_to_date_cost=95.0))
        service = _service(maker, billing, credit_usd=credit_usd)

        assert await service.try_charge("fleet_routing", 1760, 52.8) is approved

    @pytest.mark.parametrize(
        ("credits_used", "cost", "approved"),
        [
            # $10 of credit left plus $80 of budget covers $90.
            (-240.0, 90.0, True),
            (-240.0, 90.01, False),
            # Credits beyond the monthly grant leave none, never less than none.
            (-400.0, 80.0, True),
            (-400.0, 80.01, False),
        ],
    )
    async def test_only_the_remaining_credit_absorbs(
        self, maker: Any, credits_used: float, cost: float, approved: bool
    ) -> None:
        billing = FakeBilling(_summary(credits=credits_used))
        service = _service(maker, billing, credit_usd=250.0)

        assert await service.try_charge("t", 1, cost) is approved


class TestCurrency:
    """Maps prices are in USD; spend and budget are in the account's currency."""

    @pytest.mark.parametrize(("cost_usd", "approved"), [(50.0, True), (50.01, False)])
    async def test_converts_the_estimate_into_the_billing_currency(
        self, maker: Any, cost_usd: float, approved: bool
    ) -> None:
        billing = FakeBilling(
            _summary(
                currency="CAD",
                budget_currency="CAD",
                usd_conversion_rate=1.4,
                month_to_date_cost=0.0,
                budget_amount=70.0,
            )
        )

        assert await _service(maker, billing).try_charge("t", 1, cost_usd) is approved

    async def test_converts_used_credit_back_into_usd(self, maker: Any) -> None:
        """C$280 of credit used is $200 of a $250 grant, leaving $50."""
        billing = FakeBilling(
            _summary(
                credits=-280.0,
                usd_conversion_rate=1.4,
                month_to_date_cost=0.0,
                budget_amount=0.0,
            )
        )
        service = _service(maker, billing, credit_usd=250.0)

        assert await service.try_charge("t", 1, 50.0)
        assert not await service.try_charge("t", 1, 0.01)

    async def test_no_rate_yet_is_fine_for_a_usd_account(self, maker: Any) -> None:
        billing = FakeBilling(_summary(usd_conversion_rate=None))

        assert await _service(maker, billing).try_charge("t", 1, 1.0)

    async def test_no_rate_yet_refuses_any_other_currency(self, maker: Any) -> None:
        billing = FakeBilling(
            _summary(usd_conversion_rate=None, currency="", budget_currency="CAD")
        )

        assert not await _service(maker, billing).try_charge("t", 1, 1.0)


class TestPendingCharges:
    """Charges the export has not caught up with still count."""

    async def test_recent_charges_count_against_the_budget(self, maker: Any) -> None:
        service = _service(maker)
        assert await service.try_charge("t", 1, 50.0)

        assert not await service.try_charge("t", 1, 30.01)
        assert await service.try_charge("t", 1, 30.0)

    async def test_charges_within_the_lag_of_the_last_export_still_count(
        self, maker: Any
    ) -> None:
        """The export's refresh time does not prove it covers earlier usage."""
        as_of = now_utc() - timedelta(hours=2)
        await _add_charge(maker, 50.0, as_of - EXPORT_LAG + timedelta(minutes=5))
        billing = FakeBilling(_summary(data_as_of=as_of))

        assert not await _service(maker, billing).try_charge("t", 1, 30.01)

    async def test_charges_well_before_the_last_export_are_in_its_total(
        self, maker: Any
    ) -> None:
        as_of = now_utc() - timedelta(hours=2)
        await _add_charge(maker, 50.0, as_of - EXPORT_LAG - timedelta(minutes=5))
        billing = FakeBilling(_summary(data_as_of=as_of))

        assert await _service(maker, billing).try_charge("t", 1, 80.0)

    async def test_without_an_export_every_charge_this_month_counts(
        self, maker: Any
    ) -> None:
        month_start = now_local().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        await _add_charge(maker, 50.0, month_start + timedelta(minutes=1))
        await _add_charge(maker, 500.0, month_start - timedelta(minutes=1))
        billing = FakeBilling(_summary(data_as_of=None))

        assert not await _service(maker, billing).try_charge("t", 1, 30.01)
        assert await _service(maker, billing).try_charge("t", 1, 30.0)

    async def test_pending_charges_use_up_the_credit_first(self, maker: Any) -> None:
        service = _service(maker, credit_usd=100.0)
        assert await service.try_charge("t", 1, 100.0)  # all credit

        assert not await service.try_charge("t", 1, 80.01)
        assert await service.try_charge("t", 1, 80.0)


class TestUnreadableBilling:
    """Without a budget to check against, paid tiers are never approved."""

    @pytest.mark.parametrize(
        "error",
        [
            BillingError("export table not found"),
            TimeoutError(),
            RuntimeError("unexpected"),
        ],
    )
    async def test_a_billing_failure_refuses(self, maker: Any, error: Any) -> None:
        service = _service(maker, FakeBilling(error=error))

        assert not await service.try_charge("t", 1, 0.01)
        assert await _charges(maker) == []

    async def test_no_budget_configured_refuses(self, maker: Any) -> None:
        billing = FakeBilling(_summary(budget_amount=None))

        assert not await _service(maker, billing).try_charge("t", 1, 0.01)


class TestPinnedCharge:
    async def test_records_whatever_the_budget_says(self, maker: Any) -> None:
        service = _service(maker, FakeBilling(_summary(month_to_date_cost=999.0)))

        await service.charge("fleet_routing", 87, 2.61)

        assert await _charges(maker) == [("fleet_routing", 87, 2.61)]

    async def test_pinned_charges_count_against_later_checks(self, maker: Any) -> None:
        service = _service(maker)
        await service.charge("fleet_routing", 1, 70.0)

        assert not await service.try_charge("t", 1, 10.01)


class TestConcurrency:
    async def test_racing_checks_never_overspend(self, maker: Any) -> None:
        """Ten $20 calls race for $80 of room. Separate sessions, real
        Postgres: without the lock, every racer reads the same total."""
        service = _service(maker)

        results = await asyncio.gather(
            *(service.try_charge("t", 1, 20.0) for _ in range(10))
        )

        assert sum(results) == 4
        assert len(await _charges(maker)) == 4

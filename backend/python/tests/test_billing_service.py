"""Tests for the billing service's composition of budget and cost."""

from datetime import datetime
from typing import Any

import pytest

from app.config import settings
from app.services.implementations.billing_service import BillingService
from app.utilities.billing_client import BillingError, BudgetInfo, CostInfo

pytestmark = pytest.mark.asyncio


class _FakeBillingClient:
    """Billing client returning fixed values, or raising on budget lookup."""

    def __init__(self, budget_error: Exception | None = None) -> None:
        self.budget_error = budget_error

    def fetch_month_to_date_cost(self, _now: datetime) -> CostInfo:
        return CostInfo(
            gross_cost=100.0,
            credits=-25.0,
            currency="CAD",
            last_export_time=datetime(2026, 7, 29, 15, 0),
        )

    def fetch_budget(self) -> BudgetInfo | None:
        if self.budget_error is not None:
            raise self.budget_error
        return BudgetInfo(
            amount=500.0, currency="CAD", display_name="Monthly", scope="project"
        )


def _service(budget_error: Exception | None = None) -> BillingService:
    import logging

    return BillingService(logging.getLogger(__name__), _FakeBillingClient(budget_error))  # type: ignore[arg-type]


class TestMonthToDateSummary:
    """Budget and cost are combined into one summary."""

    async def test_composes_budget_and_cost(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "billing_target_project_id", "f4k-123")

        summary = await _service().get_month_to_date_summary()

        assert summary.project_id == "f4k-123"
        assert summary.gross_cost == 100.0
        assert summary.credits == -25.0
        assert summary.month_to_date_cost == 75.0
        assert summary.budget_amount == 500.0
        assert summary.budget_scope == "project"
        assert summary.data_as_of == datetime(2026, 7, 29, 15, 0)

    async def test_invoice_month_is_formatted_for_display(self) -> None:
        summary = await _service().get_month_to_date_summary()

        assert len(summary.invoice_month) == 7
        assert summary.invoice_month[4] == "-"


class TestBudgetDegradation:
    """A budget failure must not cost us the spend figure."""

    @pytest.mark.parametrize(
        "error", [BillingError("permission denied"), TimeoutError()]
    )
    async def test_costs_still_returned_when_budget_lookup_fails(
        self, error: Exception
    ) -> None:
        summary = await _service(error).get_month_to_date_summary()

        assert summary.month_to_date_cost == 75.0
        assert summary.budget_amount is None
        assert summary.budget_scope is None
        assert summary.budget_currency is None

    async def test_cost_failure_still_propagates(self) -> None:
        """Costs are the point of the endpoint, so their failure is fatal."""

        class _Failing(_FakeBillingClient):
            def fetch_month_to_date_cost(self, _now: datetime) -> CostInfo:
                raise BillingError("export table not found")

        import logging

        service = BillingService(logging.getLogger(__name__), _Failing())  # type: ignore[arg-type]

        with pytest.raises(BillingError):
            await service.get_month_to_date_summary()


class TestNoCaching:
    """The contract is a live query per request."""

    async def test_each_call_requeries_the_client(self) -> None:
        calls: list[Any] = []

        class _Counting(_FakeBillingClient):
            def fetch_month_to_date_cost(self, now: datetime) -> CostInfo:
                calls.append(now)
                return super().fetch_month_to_date_cost(now)

        import logging

        service = BillingService(logging.getLogger(__name__), _Counting())  # type: ignore[arg-type]

        await service.get_month_to_date_summary()
        await service.get_month_to_date_summary()

        assert len(calls) == 2

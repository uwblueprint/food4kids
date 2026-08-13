"""Tests for the Cloud Billing client.

Exercises budget selection and result parsing directly, without network, in the
style of ``test_google_maps_routing_service.py``.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytest
from google.api_core import exceptions as gcp_exceptions

from app.config import settings
from app.utilities.billing_client import (
    PARTITION_LOOKBACK_DAYS,
    BillingClient,
    BillingError,
    BillingNotConfiguredError,
    CostInfo,
)


def _raise(error: Exception) -> Any:
    """Build a stand-in callable that raises when the client calls into the SDK."""

    def _fail(*_args: Any, **_kwargs: Any) -> Any:
        raise error

    return _fail


@dataclass
class FakeRow:
    """Stand-in for a BigQuery result row."""

    gross_cost: float | None
    credit_amount: float | None
    currency: str | None
    last_export_time: datetime | None


def _budget(
    amount: dict[str, Any] | None = None, projects: list[str] | None = None
) -> dict[str, Any]:
    """Build a Budget resource as the Budget API would return it."""
    return {
        "displayName": "Monthly budget",
        "amount": amount
        if amount is not None
        else {"specifiedAmount": {"units": "50"}},
        "budgetFilter": {"projects": projects} if projects else {},
    }


@pytest.fixture
def client() -> BillingClient:
    import logging

    return BillingClient(logging.getLogger(__name__))


class TestSelectBudget:
    """Budget selection prefers the most specific match."""

    def test_prefers_project_scoped_over_account_wide(
        self, client: BillingClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "billing_target_project_id", "f4k-123")

        result = client._select_budget(
            [
                _budget({"specifiedAmount": {"units": "500"}}),
                _budget({"specifiedAmount": {"units": "50"}}, ["projects/f4k-123"]),
            ]
        )

        assert result is not None
        assert result.amount == 50.0
        assert result.scope == "project"

    def test_falls_back_to_account_wide(
        self, client: BillingClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "billing_target_project_id", "f4k-123")

        result = client._select_budget([_budget({"specifiedAmount": {"units": "500"}})])

        assert result is not None
        assert result.amount == 500.0
        assert result.scope == "billing_account"

    def test_ignores_budget_for_a_different_project(
        self, client: BillingClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "billing_target_project_id", "f4k-123")

        assert client._select_budget([_budget(projects=["projects/other"])]) is None

    def test_returns_none_when_no_budgets_exist(self, client: BillingClient) -> None:
        assert client._select_budget([]) is None

    def test_largest_wins_among_several_account_wide_budgets(
        self, client: BillingClient
    ) -> None:
        """The real account carries a $1 alert alongside the $20 ceiling.

        Picking by list order would make the reported budget depend on whatever
        order the API returned.
        """
        result = client._select_budget(
            [
                _budget({"specifiedAmount": {"units": "1"}}),
                _budget({"specifiedAmount": {"units": "20"}}),
            ]
        )

        assert result is not None
        assert result.amount == 20.0

    def test_order_does_not_affect_the_choice(self, client: BillingClient) -> None:
        low = _budget({"specifiedAmount": {"units": "1"}})
        high = _budget({"specifiedAmount": {"units": "20"}})

        forward = client._select_budget([low, high])
        reversed_ = client._select_budget([high, low])

        assert forward is not None and reversed_ is not None
        assert forward.amount == reversed_.amount == 20.0

    def test_project_scope_beats_a_larger_account_wide_budget(
        self, client: BillingClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Specificity outranks size — a project budget is the better match."""
        monkeypatch.setattr(settings, "billing_target_project_id", "f4k-123")

        result = client._select_budget(
            [
                _budget({"specifiedAmount": {"units": "9999"}}),
                _budget({"specifiedAmount": {"units": "20"}}, ["projects/f4k-123"]),
            ]
        )

        assert result is not None
        assert result.amount == 20.0
        assert result.scope == "project"

    def test_combines_units_and_nanos(self, client: BillingClient) -> None:
        result = client._select_budget(
            [_budget({"specifiedAmount": {"units": "50", "nanos": 500000000}})]
        )

        assert result is not None
        assert result.amount == pytest.approx(50.5)

    def test_last_period_budget_has_no_reportable_amount(
        self, client: BillingClient
    ) -> None:
        """lastPeriodAmount carries no figure, so there is nothing to surface."""
        assert client._select_budget([_budget({"lastPeriodAmount": {}})]) is None


class TestParseCostRow:
    """Cost parsing tolerates the empty-month case."""

    def test_subtracts_credits_from_gross(self) -> None:
        row = FakeRow(
            gross_cost=100.0,
            credit_amount=-25.0,
            currency="CAD",
            last_export_time=datetime(2026, 7, 29, 15, 0),
        )

        cost = BillingClient._parse_cost_row(row)

        assert cost.gross_cost == 100.0
        assert cost.credits == -25.0
        assert cost.net_cost == 75.0
        assert cost.currency == "CAD"

    def test_no_rows_reads_as_zero(self) -> None:
        cost = BillingClient._parse_cost_row(None)

        assert cost == CostInfo(
            gross_cost=0.0, credits=0.0, currency="", last_export_time=None
        )

    def test_month_with_no_usage_aggregates_to_nulls(self) -> None:
        """SUM over zero rows yields one all-NULL row rather than no rows."""
        row = FakeRow(
            gross_cost=None, credit_amount=None, currency=None, last_export_time=None
        )

        cost = BillingClient._parse_cost_row(row)

        assert cost.net_cost == 0.0
        assert cost.currency == ""


class TestConfigurationGuards:
    """Missing configuration fails loudly and distinctly from a call failure."""

    def test_missing_service_account_raises(
        self, client: BillingClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "billing_service_account_client_email", "")

        with pytest.raises(BillingNotConfiguredError, match="BILLING_"):
            client._ensure_credentials()

    def test_missing_billing_account_raises(
        self, client: BillingClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "billing_account_id", "")

        with pytest.raises(BillingNotConfiguredError, match="BILLING_ACCOUNT_ID"):
            client.fetch_budget()

    @pytest.mark.parametrize(
        ("blank_field", "expected"),
        [
            ("billing_export_dataset", "BILLING_EXPORT_DATASET"),
            ("billing_export_table", "BILLING_EXPORT_TABLE"),
            ("billing_target_project_id", "BILLING_TARGET_PROJECT_ID"),
        ],
    )
    def test_missing_export_config_raises(
        self,
        client: BillingClient,
        monkeypatch: pytest.MonkeyPatch,
        blank_field: str,
        expected: str,
    ) -> None:
        for field in (
            "billing_export_dataset",
            "billing_export_table",
            "billing_target_project_id",
        ):
            monkeypatch.setattr(settings, field, "set")
        monkeypatch.setattr(settings, blank_field, "")

        with pytest.raises(BillingNotConfiguredError, match=expected):
            client.fetch_month_to_date_cost(datetime(2026, 7, 29))


class TestPartitionLookback:
    """The partition filter must never be tighter than the month start."""

    def test_lookback_precedes_month_start(self) -> None:
        assert PARTITION_LOOKBACK_DAYS > 0


@pytest.fixture
def configured(client: BillingClient, monkeypatch: pytest.MonkeyPatch) -> BillingClient:
    """A client with settings populated and credentials stubbed out."""
    for field in (
        "billing_account_id",
        "billing_export_dataset",
        "billing_export_table",
        "billing_target_project_id",
        "billing_service_account_client_email",
    ):
        monkeypatch.setattr(settings, field, "set")
    monkeypatch.setattr(client, "_ensure_credentials", lambda: object())
    return client


class TestErrorMapping:
    """SDK failures collapse to BillingError with a message the router can key on.

    The router maps to 403 by looking for "permission denied" in the message, so
    that wording is load-bearing rather than cosmetic.
    """

    def test_budget_forbidden_says_permission_denied(
        self, configured: BillingClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "app.utilities.billing_client.build",
            _raise(gcp_exceptions.Forbidden("nope")),
        )

        with pytest.raises(BillingError, match="permission denied"):
            configured.fetch_budget()

    def test_budget_not_found_is_reported_as_such(
        self, configured: BillingClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "app.utilities.billing_client.build",
            _raise(gcp_exceptions.NotFound("gone")),
        )

        with pytest.raises(BillingError, match="not found"):
            configured.fetch_budget()

    def test_unexpected_budget_error_does_not_leak_detail(
        self, configured: BillingClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "app.utilities.billing_client.build",
            _raise(RuntimeError("connection string with a password in it")),
        )

        with pytest.raises(BillingError) as excinfo:
            configured.fetch_budget()

        assert "password" not in str(excinfo.value)

    def test_cost_forbidden_says_permission_denied(
        self, configured: BillingClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "app.utilities.billing_client.bigquery.Client",
            _raise(gcp_exceptions.Forbidden("nope")),
        )

        with pytest.raises(BillingError, match="permission denied"):
            configured.fetch_month_to_date_cost(datetime(2026, 7, 29))

    def test_missing_export_table_hints_at_setup(
        self, configured: BillingClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The likeliest cause is that billing export was never enabled."""
        monkeypatch.setattr(
            "app.utilities.billing_client.bigquery.Client",
            _raise(gcp_exceptions.NotFound("gone")),
        )

        with pytest.raises(BillingError, match="export"):
            configured.fetch_month_to_date_cost(datetime(2026, 7, 29))

    def test_unexpected_cost_error_does_not_leak_detail(
        self, configured: BillingClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "app.utilities.billing_client.bigquery.Client",
            _raise(RuntimeError("connection string with a password in it")),
        )

        with pytest.raises(BillingError) as excinfo:
            configured.fetch_month_to_date_cost(datetime(2026, 7, 29))

        assert "password" not in str(excinfo.value)

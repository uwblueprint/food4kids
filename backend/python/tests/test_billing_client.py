"""Tests for the Cloud Billing client.

Exercises budget selection and result parsing directly, without network, in the
style of ``test_google_maps_routing_service.py``.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from google.api_core import exceptions as gcp_exceptions

from app.config import settings
from app.utilities.billing_client import (
    PARTITION_LOOKBACK_DAYS,
    BillingClient,
    BillingError,
    BillingNotConfiguredError,
    BillingPermissionDeniedError,
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
    # Caching off by default so each test's calls actually reach the fake;
    # the cache tests below opt back in.
    monkeypatch.setattr(settings, "billing_cache_ttl_seconds", 0)
    return client


class TestErrorMapping:
    """SDK failures collapse to BillingError, with a distinct type for 403s.

    The router keys off ``BillingPermissionDeniedError`` rather than the message
    text, so these assert the type; the wording is only for the operator.
    """

    def test_budget_forbidden_says_permission_denied(
        self, configured: BillingClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "app.utilities.billing_client.build",
            _raise(gcp_exceptions.Forbidden("nope")),
        )

        with pytest.raises(BillingPermissionDeniedError, match="permission denied"):
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

        with pytest.raises(BillingPermissionDeniedError, match="permission denied"):
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


class _FakeQueryJob:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def result(self) -> list[Any]:
        return self._rows


class _FakeBQClient:
    """Records every query so tests can count how many actually ran."""

    def __init__(self) -> None:
        self.job_configs: list[Any] = []

    def query(self, _query: str, job_config: Any = None) -> _FakeQueryJob:
        self.job_configs.append(job_config)
        return _FakeQueryJob([FakeRow(1.0, -0.25, "CAD", datetime(2026, 7, 29))])


@pytest.fixture
def fake_bq(monkeypatch: pytest.MonkeyPatch) -> tuple[_FakeBQClient, list[int]]:
    """Patch bigquery.Client, returning the fake and a construction counter."""
    fake = _FakeBQClient()
    constructions = [0]

    def _factory(*_args: Any, **_kwargs: Any) -> _FakeBQClient:
        constructions[0] += 1
        return fake

    monkeypatch.setattr("app.utilities.billing_client.bigquery.Client", _factory)
    return fake, constructions


def _partition_floor(job_config: Any) -> datetime:
    """Pull the bound ``partition_floor`` value out of a captured job config."""
    by_name = {p.name: p.value for p in job_config.query_parameters}
    return by_name["partition_floor"]  # type: ignore[no-any-return]


class TestPartitionLookback:
    """The partition filter must never be tighter than the month start.

    `_PARTITIONTIME` can lag a row's usage time, so the floor exists to trim
    scanned bytes without dropping rows. A floor landing after the true month
    start would undercount the month with no error raised.
    """

    @pytest.mark.parametrize(
        "zone", ["America/New_York", "UTC", "Asia/Kolkata", "Australia/Sydney"]
    )
    def test_floor_precedes_month_start_in_every_zone(
        self,
        configured: BillingClient,
        fake_bq: tuple[_FakeBQClient, list[int]],
        zone: str,
    ) -> None:
        """Zones ahead of UTC are the ones a naive floor silently narrows."""
        now = datetime(2026, 7, 29, 3, 0, tzinfo=ZoneInfo(zone))
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fake, _ = fake_bq

        configured.fetch_month_to_date_cost(now)

        floor = _partition_floor(fake.job_configs[0])
        assert floor.tzinfo is not None, "BigQuery reads a naive TIMESTAMP as UTC"
        assert floor < month_start
        assert month_start - floor == timedelta(days=PARTITION_LOOKBACK_DAYS)


class TestQueryCost:
    """Guards against a polling caller running up a surprise BigQuery bill."""

    def test_query_caps_bytes_billed(
        self,
        configured: BillingClient,
        fake_bq: tuple[_FakeBQClient, list[int]],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(settings, "billing_max_bytes_billed", 12345)
        fake, _ = fake_bq

        configured.fetch_month_to_date_cost(datetime(2026, 7, 29))

        assert fake.job_configs[0].maximum_bytes_billed == 12345

    def test_bigquery_client_is_built_once_and_reused(
        self, configured: BillingClient, fake_bq: tuple[_FakeBQClient, list[int]]
    ) -> None:
        _, constructions = fake_bq

        configured.fetch_month_to_date_cost(datetime(2026, 7, 29))
        configured.fetch_month_to_date_cost(datetime(2026, 7, 30))

        assert constructions[0] == 1


class TestCostCaching:
    """A short TTL costs no accuracy — the export only refreshes every few hours."""

    def test_second_call_within_ttl_does_not_requery(
        self,
        configured: BillingClient,
        fake_bq: tuple[_FakeBQClient, list[int]],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(settings, "billing_cache_ttl_seconds", 300)
        fake, _ = fake_bq

        first = configured.fetch_month_to_date_cost(datetime(2026, 7, 29))
        second = configured.fetch_month_to_date_cost(datetime(2026, 7, 29))

        assert len(fake.job_configs) == 1
        assert first == second

    def test_zero_ttl_queries_every_time(
        self,
        configured: BillingClient,
        fake_bq: tuple[_FakeBQClient, list[int]],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Setting the TTL to 0 restores the original live-per-request contract."""
        monkeypatch.setattr(settings, "billing_cache_ttl_seconds", 0)
        fake, _ = fake_bq

        configured.fetch_month_to_date_cost(datetime(2026, 7, 29))
        configured.fetch_month_to_date_cost(datetime(2026, 7, 29))

        assert len(fake.job_configs) == 2

    def test_expired_entry_requeries(
        self,
        configured: BillingClient,
        fake_bq: tuple[_FakeBQClient, list[int]],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(settings, "billing_cache_ttl_seconds", 300)
        fake, _ = fake_bq
        clock = [1000.0]
        monkeypatch.setattr(
            "app.utilities.billing_client.time.monotonic", lambda: clock[0]
        )

        configured.fetch_month_to_date_cost(datetime(2026, 7, 29))
        clock[0] += 301
        configured.fetch_month_to_date_cost(datetime(2026, 7, 29))

        assert len(fake.job_configs) == 2

    def test_a_new_invoice_month_is_never_served_from_cache(
        self,
        configured: BillingClient,
        fake_bq: tuple[_FakeBQClient, list[int]],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Rolling into a new month must not report the old month's total."""
        monkeypatch.setattr(settings, "billing_cache_ttl_seconds", 300)
        fake, _ = fake_bq

        configured.fetch_month_to_date_cost(datetime(2026, 7, 31))
        configured.fetch_month_to_date_cost(datetime(2026, 8, 1))

        assert len(fake.job_configs) == 2


class TestBudgetCaching:
    """The budget changes far less often than the cost, but shares the TTL."""

    def _patch_budget_api(
        self, monkeypatch: pytest.MonkeyPatch, calls: list[int]
    ) -> None:
        class _Budgets:
            def list(self, **_kwargs: Any) -> Any:
                return self

            def execute(self) -> dict[str, Any]:
                calls[0] += 1
                return {"budgets": [_budget({"specifiedAmount": {"units": "20"}})]}

        class _Accounts:
            def budgets(self) -> _Budgets:
                return _Budgets()

        class _Service:
            def billingAccounts(self) -> _Accounts:
                return _Accounts()

        monkeypatch.setattr(
            "app.utilities.billing_client.build", lambda *_a, **_k: _Service()
        )

    def test_second_call_within_ttl_does_not_refetch(
        self, configured: BillingClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "billing_cache_ttl_seconds", 300)
        calls = [0]
        self._patch_budget_api(monkeypatch, calls)

        first = configured.fetch_budget()
        second = configured.fetch_budget()

        assert calls[0] == 1
        assert first == second

    def test_zero_ttl_refetches(
        self, configured: BillingClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "billing_cache_ttl_seconds", 0)
        calls = [0]
        self._patch_budget_api(monkeypatch, calls)

        configured.fetch_budget()
        configured.fetch_budget()

        assert calls[0] == 2

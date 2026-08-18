"""Tests for GET /billing/costs.

External failures are simulated by swapping the billing service via
``client_with_overrides``; the assertions are about status mapping and that no
upstream detail reaches the client.
"""

from datetime import datetime
from typing import Any

import pytest

from app.dependencies.services import get_billing_service
from app.services.implementations.billing_service import BillingSummary
from app.utilities.billing_client import (
    BillingError,
    BillingNotConfiguredError,
    BillingPermissionDeniedError,
)

# pytest.ini's asyncio_mode=auto sits under a [tool:pytest] header and so is not
# read; async tests need the marker explicitly, as elsewhere in this suite.
pytestmark = pytest.mark.asyncio

ENDPOINT = "/billing/costs"


def _summary() -> BillingSummary:
    return BillingSummary(
        project_id="food4kids-473501",
        invoice_month="2026-07",
        currency="CAD",
        month_to_date_cost=75.0,
        gross_cost=100.0,
        credits=-25.0,
        budget_amount=500.0,
        budget_currency="CAD",
        budget_display_name="Monthly budget",
        budget_scope="project",
        data_as_of=datetime(2026, 7, 29, 15, 0),
    )


class _FakeBillingService:
    """Billing service that returns a fixed summary or raises."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    async def get_month_to_date_summary(self) -> BillingSummary:
        if self.error is not None:
            raise self.error
        return _summary()


def _override(error: Exception | None = None) -> dict[Any, Any]:
    service = _FakeBillingService(error)
    return {get_billing_service: lambda: service}


class TestGetBillingCosts:
    """The happy path returns budget and month-to-date spend."""

    async def test_returns_costs_and_budget(self, client_with_overrides: Any) -> None:
        client = await client_with_overrides(_override())

        response = await client.get(ENDPOINT)

        assert response.status_code == 200
        body = response.json()
        assert body["project_id"] == "food4kids-473501"
        assert body["invoice_month"] == "2026-07"
        assert body["month_to_date_cost"] == 75.0
        assert body["gross_cost"] == 100.0
        assert body["credits"] == -25.0
        assert body["budget_amount"] == 500.0
        assert body["budget_scope"] == "project"
        assert body["data_as_of"] is not None

    async def test_reports_freshness_so_callers_do_not_imply_live_data(
        self, client_with_overrides: Any
    ) -> None:
        """Cost data lags by hours; data_as_of is how a caller conveys that."""
        client = await client_with_overrides(_override())

        body = (await client.get(ENDPOINT)).json()

        assert body["data_as_of"].startswith("2026-07-29T15:00:00")


class TestBillingCostsFailures:
    """Upstream problems map to a status the caller can act on."""

    async def test_unconfigured_returns_503(self, client_with_overrides: Any) -> None:
        client = await client_with_overrides(
            _override(
                BillingNotConfiguredError("Billing integration is not configured.")
            )
        )

        response = await client.get(ENDPOINT)

        assert response.status_code == 503
        assert "not configured" in response.json()["detail"]

    async def test_permission_denied_returns_403(
        self, client_with_overrides: Any
    ) -> None:
        client = await client_with_overrides(
            _override(
                BillingPermissionDeniedError("Cost query failed: permission denied.")
            )
        )

        assert (await client.get(ENDPOINT)).status_code == 403

    async def test_upstream_failure_returns_503_not_500(
        self, client_with_overrides: Any
    ) -> None:
        """A third-party outage is not our internal error."""
        client = await client_with_overrides(
            _override(
                BillingError("Cost query failed: billing export table not found.")
            )
        )

        assert (await client.get(ENDPOINT)).status_code == 503

    async def test_timeout_returns_503(self, client_with_overrides: Any) -> None:
        client = await client_with_overrides(_override(TimeoutError()))

        response = await client.get(ENDPOINT)

        assert response.status_code == 503
        assert response.json()["detail"] == "Billing lookup timed out."

    async def test_unexpected_error_does_not_leak_detail(
        self, client_with_overrides: Any
    ) -> None:
        """Anything not a BillingError falls through to the 500 middleware.

        The handler must not catch it and re-emit the message as a detail
        string, which is how internal text has leaked before (see #216).
        """
        secret = "internal db password is hunter2"
        client = await client_with_overrides(_override(RuntimeError(secret)))

        response = await client.get(ENDPOINT)

        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error"}
        assert secret not in response.text

"""Cloud Billing client: budget amount from the Budget API, spend from BigQuery.

Two sources are needed because no Google API returns accrued spend. The Cloud
Billing API (cloudbilling.googleapis.com) only exposes account metadata and the
SKU price list, and the Budget API returns a budget's *configured* amount but not
the cost against it. The only source of actual cost is the Cloud Billing export
to BigQuery, which is also why the numbers lag by hours — the export refreshes
throughout the day rather than in real time.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from google.api_core import exceptions as gcp_exceptions
from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.config import settings

if TYPE_CHECKING:
    import logging
    from collections.abc import Mapping, Sequence

SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

# The export table is partitioned on _PARTITIONTIME, which can lag a row's usage
# time. Floor the partition scan this far before the month start so the filter
# only trims cost, never rows.
PARTITION_LOOKBACK_DAYS = 2

T = TypeVar("T")


class _TimedCache(Generic[T]):
    """Single-value cache with a TTL, safe to read from worker threads.

    Both lookups run under ``asyncio.to_thread``, so several requests can land
    here concurrently. A TTL of zero disables caching entirely.
    """

    def __init__(self) -> None:
        self._entry: tuple[str, T, float] | None = None
        self._lock = threading.Lock()

    def get(self, key: str) -> tuple[bool, T | None]:
        """Return ``(hit, value)``. ``hit`` distinguishes a cached ``None``."""
        if settings.billing_cache_ttl_seconds <= 0:
            return False, None
        with self._lock:
            if self._entry is None:
                return False, None
            cached_key, value, expires_at = self._entry
            if cached_key != key or time.monotonic() >= expires_at:
                return False, None
            return True, value

    def set(self, key: str, value: T) -> None:
        if settings.billing_cache_ttl_seconds <= 0:
            return
        with self._lock:
            expiry = time.monotonic() + settings.billing_cache_ttl_seconds
            self._entry = (key, value, expiry)

    def clear(self) -> None:
        with self._lock:
            self._entry = None


class BillingError(Exception):
    """Raised when a billing lookup fails; safe to expose detail strings to API clients."""


class BillingNotConfiguredError(BillingError):
    """Raised when the BILLING_* settings are absent."""


class BillingPermissionDeniedError(BillingError):
    """Raised when the billing service account lacks a required role.

    Its own type so the router can map it to 403 without matching on the
    message text, which would break silently if the wording changed.
    """


@dataclass
class BudgetInfo:
    """A budget as configured in Cloud Billing."""

    amount: float
    currency: str
    display_name: str
    # "project" when the budget is filtered to our target project, otherwise
    # "billing_account" — an account-wide budget is not directly comparable to
    # project-scoped spend, so callers need to know which they got.
    scope: str


@dataclass
class CostInfo:
    """Month-to-date cost for a single project, as of the export's last refresh."""

    gross_cost: float
    credits: float
    currency: str
    last_export_time: datetime | None

    @property
    def net_cost(self) -> float:
        """Cost after credits. Credits are stored negative, so this adds them."""
        return self.gross_cost + self.credits


class BillingClient:
    """Reads the configured budget and month-to-date spend from Google Cloud."""

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self._credentials: service_account.Credentials | None = None
        self._bq_client: bigquery.Client | None = None
        # Reentrant: _ensure_bq_client holds this while calling
        # _ensure_credentials, which takes it again.
        self._credentials_lock = threading.RLock()
        self._cost_cache: _TimedCache[CostInfo] = _TimedCache()
        self._budget_cache: _TimedCache[BudgetInfo | None] = _TimedCache()

    def _ensure_credentials(self) -> service_account.Credentials:
        """Build (once) the dedicated billing service account credentials."""
        with self._credentials_lock:
            if self._credentials is not None:
                return self._credentials

            if not settings.billing_service_account_client_email:
                raise BillingNotConfiguredError(
                    "Billing integration is not configured. "
                    "Set the BILLING_* environment variables."
                )

            self._credentials = service_account.Credentials.from_service_account_info(
                {
                    "type": "service_account",
                    "project_id": settings.billing_target_project_id,
                    "private_key_id": settings.billing_service_account_private_key_id,
                    "private_key": settings.billing_service_account_private_key.replace(
                        "\\n", "\n"
                    ).strip(),
                    "client_email": settings.billing_service_account_client_email,
                    "client_id": settings.billing_service_account_client_id,
                    "auth_uri": settings.billing_service_account_auth_uri,
                    "token_uri": settings.billing_service_account_token_uri,
                    "auth_provider_x509_cert_url": settings.billing_service_account_auth_provider_x509_cert_url,
                },
                scopes=SCOPES,
            )
            return self._credentials

    def _ensure_bq_client(self) -> bigquery.Client:
        """Build the BigQuery client once and reuse it across requests.

        Constructing one per call re-does credential and transport setup on
        every request for no benefit — the client is safe to share.
        """
        with self._credentials_lock:
            if self._bq_client is None:
                self._bq_client = bigquery.Client(
                    credentials=self._ensure_credentials(),
                    project=settings.billing_target_project_id,
                )
            return self._bq_client

    def fetch_budget(self) -> BudgetInfo | None:
        """Return the budget for our target project, or None if none is set.

        Prefers a budget explicitly filtered to the target project; falls back to
        account-wide budgets so a single shared budget still surfaces.
        """
        if not settings.billing_account_id:
            raise BillingNotConfiguredError(
                "Billing account is not configured. Set BILLING_ACCOUNT_ID."
            )

        hit, cached = self._budget_cache.get(settings.billing_account_id)
        if hit:
            return cached

        credentials = self._ensure_credentials()

        try:
            service = build(
                "billingbudgets", "v1", credentials=credentials, cache_discovery=False
            )
            response = (
                service.billingAccounts()
                .budgets()
                .list(parent=f"billingAccounts/{settings.billing_account_id}")
                .execute()
            )
        except gcp_exceptions.Forbidden as e:
            raise BillingPermissionDeniedError(
                "Budget lookup failed: permission denied. The service account "
                "needs roles/billing.viewer on the billing account."
            ) from e
        except gcp_exceptions.NotFound as e:
            raise BillingError(
                "Budget lookup failed: billing account not found."
            ) from e
        except Exception as e:
            self.logger.exception("Unexpected error fetching budget")
            raise BillingError(
                "Budget lookup failed due to an unexpected error."
            ) from e

        budget = self._select_budget(response.get("budgets", []))
        self._budget_cache.set(settings.billing_account_id, budget)
        return budget

    def _select_budget(self, budgets: Sequence[Mapping[str, Any]]) -> BudgetInfo | None:
        """Pick the most specific budget: project-scoped over account-wide.

        An account can carry several budgets — ours has a low alert threshold
        alongside the real ceiling — so within each scope the largest amount
        wins. Picking by list order would make the reported budget depend on
        whatever order the API happened to return.
        """
        target = f"projects/{settings.billing_target_project_id}"
        project_scoped: list[BudgetInfo] = []
        account_wide: list[BudgetInfo] = []

        for budget in budgets:
            projects = budget.get("budgetFilter", {}).get("projects", [])
            if target in projects:
                info = self._to_budget_info(budget, "project")
                if info is not None:
                    project_scoped.append(info)
            elif not projects:
                info = self._to_budget_info(budget, "billing_account")
                if info is not None:
                    account_wide.append(info)

        candidates = project_scoped or account_wide
        if not candidates:
            return None
        return max(candidates, key=lambda b: b.amount)

    @staticmethod
    def _to_budget_info(budget: Mapping[str, Any], scope: str) -> BudgetInfo | None:
        """Convert a Budget resource to BudgetInfo.

        Returns None for last-period budgets, which carry no fixed amount to
        report — only specifiedAmount has a figure we can show.
        """
        specified = budget.get("amount", {}).get("specifiedAmount")
        if not specified:
            return None

        # Money splits the value across whole units and nanos (1e-9 of a unit).
        units = float(specified.get("units", 0))
        nanos = float(specified.get("nanos", 0)) / 1e9

        return BudgetInfo(
            amount=units + nanos,
            currency=specified.get("currencyCode", ""),
            display_name=budget.get("displayName", ""),
            scope=scope,
        )

    def fetch_month_to_date_cost(self, now: datetime) -> CostInfo:
        """Query the billing export for spend so far in ``now``'s invoice month."""
        for name, value in (
            ("BILLING_EXPORT_DATASET", settings.billing_export_dataset),
            ("BILLING_EXPORT_TABLE", settings.billing_export_table),
            ("BILLING_TARGET_PROJECT_ID", settings.billing_target_project_id),
        ):
            if not value:
                raise BillingNotConfiguredError(
                    f"Billing export is not configured. Set {name}."
                )

        invoice_month = now.strftime("%Y%m")
        hit, cached = self._cost_cache.get(invoice_month)
        if hit and cached is not None:
            return cached

        # Stays timezone-aware: BigQuery reads a naive TIMESTAMP parameter as
        # UTC, so stripping the offset here would shift the floor by it.
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Dataset/table come from settings, never from the request, so they are
        # safe to interpolate; the filters are bound parameters.
        query = f"""
            SELECT
              SUM(cost) AS gross_cost,
              SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0))
                AS credit_amount,
              ANY_VALUE(currency) AS currency,
              MAX(export_time) AS last_export_time
            FROM `{settings.billing_target_project_id}.{settings.billing_export_dataset}.{settings.billing_export_table}`
            WHERE project.id = @project_id
              AND invoice.month = @invoice_month
              AND _PARTITIONTIME >= TIMESTAMP(@partition_floor)
        """

        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=settings.billing_max_bytes_billed,
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "project_id", "STRING", settings.billing_target_project_id
                ),
                bigquery.ScalarQueryParameter("invoice_month", "STRING", invoice_month),
                bigquery.ScalarQueryParameter(
                    "partition_floor",
                    "TIMESTAMP",
                    month_start - timedelta(days=PARTITION_LOOKBACK_DAYS),
                ),
            ],
        )

        try:
            client = self._ensure_bq_client()
            rows = list(client.query(query, job_config=job_config).result())
        except gcp_exceptions.Forbidden as e:
            raise BillingPermissionDeniedError(
                "Cost query failed: permission denied. The service account needs "
                "roles/bigquery.jobUser and roles/bigquery.dataViewer."
            ) from e
        except gcp_exceptions.NotFound as e:
            raise BillingError(
                "Cost query failed: billing export table not found. "
                "Cloud Billing export to BigQuery may not be enabled."
            ) from e
        except gcp_exceptions.BadRequest as e:
            # Most likely the maximum_bytes_billed ceiling. Say so, because the
            # fix is a config change rather than something to retry.
            self.logger.warning("Billing export query rejected: %s", e)
            raise BillingError(
                "Cost query failed: the query was rejected, possibly for "
                "exceeding the configured bytes-billed limit."
            ) from e
        except Exception as e:
            self.logger.exception("Unexpected error querying billing export")
            raise BillingError("Cost query failed due to an unexpected error.") from e

        cost = self._parse_cost_row(rows[0] if rows else None)
        self._cost_cache.set(invoice_month, cost)
        return cost

    @staticmethod
    def _parse_cost_row(row: object) -> CostInfo:
        """Build CostInfo from a result row.

        A month with no usage yet aggregates to a single all-NULL row rather than
        no rows, so both cases collapse to zero.
        """

        def _get(field: str) -> object:
            return getattr(row, field, None) if row is not None else None

        return CostInfo(
            gross_cost=float(_get("gross_cost") or 0.0),  # type: ignore[arg-type]
            credits=float(_get("credit_amount") or 0.0),  # type: ignore[arg-type]
            currency=str(_get("currency") or ""),
            last_export_time=_get("last_export_time"),  # type: ignore[arg-type]
        )

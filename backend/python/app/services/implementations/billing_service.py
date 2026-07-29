from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from app.config import settings
from app.utilities.billing_client import BillingError

if TYPE_CHECKING:
    import logging

    from app.utilities.billing_client import BillingClient, BudgetInfo

# Both calls are synchronous SDK calls run off the event loop, so they need an
# explicit ceiling. A BigQuery job on the export table is normally 1-3s.
BILLING_TIMEOUT_SECONDS = 30


@dataclass
class BillingSummary:
    """Month-to-date spend for the target project, against its budget."""

    project_id: str
    invoice_month: str
    currency: str
    month_to_date_cost: float
    gross_cost: float
    credits: float
    budget_amount: float | None
    budget_currency: str | None
    budget_display_name: str | None
    budget_scope: str | None
    data_as_of: datetime | None


class BillingService:
    """Assembles the billing summary from the Cloud Billing budget and cost export."""

    def __init__(self, logger: logging.Logger, billing_client: BillingClient) -> None:
        self.logger = logger
        self.billing_client = billing_client

    async def get_month_to_date_summary(self) -> BillingSummary:
        """Fetch budget and month-to-date spend for the configured project.

        Runs live on every call — there is no caching, per the API contract.
        """
        now = datetime.now(ZoneInfo(settings.scheduler_timezone))

        cost = await asyncio.wait_for(
            asyncio.to_thread(self.billing_client.fetch_month_to_date_cost, now),
            timeout=BILLING_TIMEOUT_SECONDS,
        )
        budget = await self._fetch_budget_or_none()

        return BillingSummary(
            project_id=settings.billing_target_project_id,
            invoice_month=now.strftime("%Y-%m"),
            currency=cost.currency,
            month_to_date_cost=cost.net_cost,
            gross_cost=cost.gross_cost,
            credits=cost.credits,
            budget_amount=budget.amount if budget else None,
            budget_currency=budget.currency if budget else None,
            budget_display_name=budget.display_name if budget else None,
            budget_scope=budget.scope if budget else None,
            data_as_of=cost.last_export_time,
        )

    async def _fetch_budget_or_none(self) -> BudgetInfo | None:
        """Look up the budget, degrading to None rather than failing the request.

        The budget is supplementary — costs are still worth returning when only
        the budget lookup fails (e.g. the service account lacks billing.viewer
        but can read the export).
        """
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self.billing_client.fetch_budget),
                timeout=BILLING_TIMEOUT_SECONDS,
            )
        except (BillingError, TimeoutError):
            self.logger.warning("Budget lookup failed; returning costs without it")
            return None

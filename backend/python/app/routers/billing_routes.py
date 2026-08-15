from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.dependencies.auth import require_admin
from app.dependencies.services import get_billing_service
from app.services.implementations.billing_service import BillingService
from app.utilities.billing_client import (
    BillingError,
    BillingNotConfiguredError,
    BillingPermissionDeniedError,
)

# Note: every other router in this app mounts at the root (/route-groups,
# /system-settings, ...). The /api segment here is specified by the billing
# ticket and is currently unique to this router.
router = APIRouter(prefix="/api/billing", tags=["billing"])


class BillingCostsResponse(BaseModel):
    project_id: str
    invoice_month: str
    currency: str
    month_to_date_cost: float
    gross_cost: float
    credits: float
    budget_amount: float | None
    budget_currency: str | None
    budget_display_name: str | None
    # "project" when the budget is filtered to this project, "billing_account"
    # when it covers the whole account and so isn't directly comparable.
    budget_scope: str | None
    # When the billing export last refreshed. Cost data lags by hours, so this
    # is what a caller should display rather than implying the figure is live.
    data_as_of: datetime | None


@router.get("/costs", response_model=BillingCostsResponse)
async def get_billing_costs(
    billing_service: BillingService = Depends(get_billing_service),
    _auth: bool = Depends(require_admin),
) -> BillingCostsResponse:
    """Return month-to-date spend for the configured project, against its budget.

    Figures come from the Cloud Billing export and typically lag by several
    hours — see ``data_as_of``. Responses are cached for
    ``BILLING_CACHE_TTL_SECONDS``, which is well under that lag.
    """
    try:
        summary = await billing_service.get_month_to_date_summary()
    except BillingNotConfiguredError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        ) from e
    except BillingPermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except BillingError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        ) from e
    except TimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Billing lookup timed out.",
        ) from e

    return BillingCostsResponse(
        project_id=summary.project_id,
        invoice_month=summary.invoice_month,
        currency=summary.currency,
        month_to_date_cost=summary.month_to_date_cost,
        gross_cost=summary.gross_cost,
        credits=summary.credits,
        budget_amount=summary.budget_amount,
        budget_currency=summary.budget_currency,
        budget_display_name=summary.budget_display_name,
        budget_scope=summary.budget_scope,
        data_as_of=summary.data_as_of,
    )

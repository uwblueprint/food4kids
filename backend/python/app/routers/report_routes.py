import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_admin
from app.models import get_session
from app.services.implementations.driver_history_service import month_bounds
from app.services.implementations.driver_report_service import DriverReportService
from app.utilities.datetime_utils import app_timezone, now_local

logger = logging.getLogger(__name__)
service = DriverReportService(logger)
router = APIRouter(prefix="/reports", tags=["reports"])


class DriverRankingItem(BaseModel):
    driver_id: str
    driver_name: str
    km: float


class MonthlyTotalsResponse(BaseModel):
    year: int
    month: int
    total_km: float
    total_deliveries: int


class TotalsResponse(BaseModel):
    total_km: float
    total_deliveries: int


MIN_SERIES_MONTHS = 1
MAX_SERIES_MONTHS = 24


def _ensure_est(dt: datetime) -> datetime:
    tz = app_timezone()
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


@router.get("/totals", response_model=TotalsResponse)
async def get_totals(
    start: datetime | None = Query(
        None, description="Start datetime, inclusive (assumed EST if no tz)"
    ),
    end: datetime | None = Query(
        None, description="End datetime, exclusive (assumed EST if no tz)"
    ),
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_admin),
) -> TotalsResponse:
    """Return km driven and deliveries made — all time, or over [start, end).

    Omit both bounds for the all-time figures the homepage's headline totals
    show. Supply both for a window: the params are read as EST when they carry
    no timezone, then reduced to calendar days (a drive date is a day, not an
    instant), and the range is half-open like every other range in the
    reports, so consecutive windows tile instead of double-counting their
    shared boundary day.
    """
    if (start is None) != (end is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start and end must be provided together",
        )

    bounds = (
        (_ensure_est(start).date(), _ensure_est(end).date())
        if start is not None and end is not None
        else None
    )

    return TotalsResponse(
        total_km=await service.get_total_km(session, bounds),
        total_deliveries=await service.get_total_deliveries(session, bounds),
    )


@router.get("/monthly-series", response_model=list[MonthlyTotalsResponse])
async def get_monthly_series(
    months: int = Query(
        6,
        ge=MIN_SERIES_MONTHS,
        le=MAX_SERIES_MONTHS,
        description="How many months to return, counting back from the end month",
    ),
    end_year: int | None = Query(
        None, description="Year of the newest month; defaults to the current month"
    ),
    end_month: int | None = Query(
        None, ge=1, le=12, description="Month of the newest month (1-12)"
    ),
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_admin),
) -> list[MonthlyTotalsResponse]:
    """Return km and deliveries per month for a trailing window, oldest first.

    Backs the homepage statistics bar charts, which need a whole series at
    once rather than one request per bar.
    """
    if (end_year is None) != (end_month is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_year and end_month must be provided together",
        )

    if end_year is None or end_month is None:
        # "The current month" is a calendar fact, so it is read on the
        # organization's clock — near midnight the two zones disagree on the
        # date, and on the 1st and the 31st they disagree on the month.
        today = now_local()
        end_year, end_month = today.year, today.month

    series = await service.get_monthly_series(session, end_year, end_month, months)
    return [MonthlyTotalsResponse(**point) for point in series]


@router.get("/monthly/{year}/{month}/ranking", response_model=list[DriverRankingItem])
async def get_monthly_ranking(
    year: int,
    month: int,
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_admin),
) -> list[DriverRankingItem]:
    """Return monthly ranking list of drivers by km (descending)."""
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid month"
        )
    rankings = await service.get_monthly_km_ranking(session, year, month)
    items: list[DriverRankingItem] = [DriverRankingItem(**r) for r in rankings]
    return items


@router.get("/monthly/{year}/{month}/totals", response_model=MonthlyTotalsResponse)
async def get_monthly_totals(
    year: int,
    month: int,
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_admin),
) -> MonthlyTotalsResponse:
    """Return total distance driven and total deliveries for the month."""
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid month"
        )
    bounds = month_bounds(year, month)
    return MonthlyTotalsResponse(
        year=year,
        month=month,
        total_km=await service.get_total_km(session, bounds),
        total_deliveries=await service.get_total_deliveries(session, bounds),
    )

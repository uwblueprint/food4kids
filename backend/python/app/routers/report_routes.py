import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies.auth import require_admin
from app.models import get_session
from app.services.implementations.driver_history_service import month_bounds
from app.services.implementations.driver_report_service import DriverReportService
from app.utilities.datetime_utils import now_utc

logger = logging.getLogger(__name__)
service = DriverReportService(logger)
router = APIRouter(prefix="/reports", tags=["reports"])


class DeliveriesCountResponse(BaseModel):
    total_deliveries: int


class DriverRankingItem(BaseModel):
    driver_id: str
    driver_name: str
    km: float


class MonthlyTotalsResponse(BaseModel):
    year: int
    month: int
    total_km: float
    total_deliveries: int


class AllTimeTotalsResponse(BaseModel):
    total_km: float
    total_deliveries: int


MIN_SERIES_MONTHS = 1
MAX_SERIES_MONTHS = 24


def _ensure_est(dt: datetime) -> datetime:
    tz = ZoneInfo(settings.scheduler_timezone)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


@router.get("/deliveries/count", response_model=DeliveriesCountResponse)
async def get_total_deliveries_between(
    start: datetime = Query(
        ..., description="Start datetime, inclusive (assumed EST if no tz)"
    ),
    end: datetime = Query(
        ..., description="End datetime, exclusive (assumed EST if no tz)"
    ),
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_admin),
) -> DeliveriesCountResponse:
    """Return total deliveries (route stop snapshots) in [start, end).

    Query params are treated as EST if no timezone is provided, then reduced
    to calendar days — a drive date is a day, not an instant. The range is
    half-open like every other range in the reports, so consecutive windows
    tile instead of double-counting their shared boundary day.
    """
    start_date = _ensure_est(start).date()
    end_date = _ensure_est(end).date()

    total = await service.get_total_deliveries(session, (start_date, end_date))
    return DeliveriesCountResponse(total_deliveries=total)


@router.get("/totals", response_model=AllTimeTotalsResponse)
async def get_all_time_totals(
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_admin),
) -> AllTimeTotalsResponse:
    """Return all-time km driven and deliveries made, across every driven route.

    Separate from /monthly-series on purpose: the homepage's headline totals
    mean "since we started", and deriving them from the chart's window would
    silently make them a trailing-N-month figure instead.
    """
    return AllTimeTotalsResponse(
        total_km=await service.get_total_km(session),
        total_deliveries=await service.get_total_deliveries(session),
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
        # "The current month" is a calendar fact, so read the UTC instant in
        # the scheduler's zone — near midnight the two disagree on the date.
        today = now_utc().astimezone(ZoneInfo(settings.scheduler_timezone))
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

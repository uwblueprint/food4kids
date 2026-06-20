import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies.auth import require_admin
from app.models import get_session
from app.services.implementations.driver_report_service import DriverReportService

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


def _ensure_est(dt: datetime) -> datetime:
    tz = ZoneInfo(settings.scheduler_timezone)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


@router.get("/deliveries/count", response_model=DeliveriesCountResponse)
async def get_total_deliveries_between(
    start: datetime = Query(..., description="Start datetime (assumed EST if no tz)"),
    end: datetime = Query(..., description="End datetime (assumed EST if no tz)"),
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_admin),
) -> DeliveriesCountResponse:
    """Return total deliveries (route stop snapshots) between start and end.
    Query params are treated as EST if no timezone is provided.
    """
    try:
        start_est = _ensure_est(start)
        end_est = _ensure_est(end)

        # Pass scheduler-timezone-aware datetimes to the service. The service
        # will normalize them to naive scheduler-local datetimes to match DB.
        total = await service.get_total_deliveries_between(session, start_est, end_est)
        return DeliveriesCountResponse(total_deliveries=total)
    except Exception as e:
        logger.exception(f"Failed to get deliveries between: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/monthly/{year}/{month}/ranking", response_model=list[DriverRankingItem])
async def get_monthly_ranking(
    year: int,
    month: int,
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_admin),
) -> list[DriverRankingItem]:
    """Return monthly ranking list of drivers by km (descending)."""
    try:
        if month < 1 or month > 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid month"
            )
        rankings = await service.get_monthly_km_ranking(session, year, month)
        items: list[DriverRankingItem] = [DriverRankingItem(**r) for r in rankings]
        return items
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get monthly ranking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/monthly/{year}/{month}/totals", response_model=MonthlyTotalsResponse)
async def get_monthly_totals(
    year: int,
    month: int,
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_admin),
) -> MonthlyTotalsResponse:
    """Return total distance driven and total deliveries for the month."""
    try:
        if month < 1 or month > 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid month"
            )
        total_km = await service.get_total_km_for_month(session, year, month)
        total_deliveries = await service.get_total_deliveries_for_month(
            session, year, month
        )
        return MonthlyTotalsResponse(
            year=year,
            month=month,
            total_km=total_km,
            total_deliveries=total_deliveries,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get monthly totals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e

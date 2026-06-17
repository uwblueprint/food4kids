import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies.auth import require_admin
from app.models import get_session
from app.services.implementations.driver_report_service import DriverReportService

logger = logging.getLogger(__name__)
service = DriverReportService(logger)
router = APIRouter(prefix="/reports", tags=["reports"])


def _ensure_est(dt: datetime) -> datetime:
    tz = ZoneInfo(settings.scheduler_timezone)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


@router.get("/deliveries/count")
async def get_total_deliveries_between(
    start: datetime = Query(..., description="Start datetime (assumed EST if no tz)"),
    end: datetime = Query(..., description="End datetime (assumed EST if no tz)"),
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_admin),
) -> dict[str, int]:
    """Return total deliveries (route stop snapshots) between start and end.
    Query params are treated as EST if no timezone is provided.
    """
    try:
        start_est = _ensure_est(start)
        end_est = _ensure_est(end)

        # Convert to UTC for DB comparisons inside service (it expects tz-aware UTC)
        start_utc = start_est.astimezone(ZoneInfo("UTC"))
        end_utc = end_est.astimezone(ZoneInfo("UTC"))

        total = await service.get_total_deliveries_between(session, start_utc, end_utc)
        return {"total_deliveries": total}
    except Exception as e:
        logger.exception(f"Failed to get deliveries between: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/monthly/{year}/{month}/ranking")
async def get_monthly_ranking(
    year: int,
    month: int,
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_admin),
) -> list[dict[str, Any]]:
    """Return monthly ranking list of drivers by km (descending)."""
    try:
        if month < 1 or month > 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid month"
            )
        rankings = await service.get_monthly_km_ranking(session, year, month)
        return rankings
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get monthly ranking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/monthly/{year}/{month}/totals")
async def get_monthly_totals(
    year: int,
    month: int,
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_admin),
) -> dict[str, Any]:
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
        return {
            "year": year,
            "month": month,
            "total_km": total_km,
            "total_deliveries": total_deliveries,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get monthly totals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e

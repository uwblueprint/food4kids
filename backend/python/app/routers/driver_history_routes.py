import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_admin, require_self_driver_or_admin
from app.models import get_session
from app.models.driver_history import (
    MAX_YEAR,
    MIN_YEAR,
    DriverHistoryAdjustmentCreate,
    DriverHistoryEntryRead,
    DriverHistoryRead,
    DriverHistorySummary,
)
from app.routers.driver_routes import get_drivers
from app.services.implementations.driver_history_csv_service import (
    DriverHistoryCSVGenerator,
)
from app.services.implementations.driver_history_service import DriverHistoryService
from app.utilities.csv_utils import generate_csv_from_list

# Initialize service
logger = logging.getLogger(__name__)
driver_history_service = DriverHistoryService(logger)

router = APIRouter(prefix="/drivers/{driver_id}/history", tags=["driver-history"])


@router.get("/summary", response_model=DriverHistorySummary)
async def get_driver_history_summary(
    driver_id: UUID,
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_self_driver_or_admin),
) -> DriverHistorySummary:
    """Get lifetime and current year KM summary for a driver"""
    try:
        if not await driver_history_service.driver_exists(session, driver_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Driver with id {driver_id} does not exist",
            )
        return await driver_history_service.get_driver_history_summary(
            session, driver_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/{year}/export", response_class=StreamingResponse)
async def export_all_drivers_history(
    driver_id: str,
    year: int,
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_admin),
) -> StreamingResponse:
    """
    Export history for all drivers for a specific year. Includes data from that year and the previous year.

    - driver_id: Must be "all"
    - year: The year to export data for
    """
    try:
        if driver_id != "all":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid driver_id: {driver_id}. Must be 'all' for year-based export",
            )

        current_year_totals = await driver_history_service.get_yearly_totals_by_driver(
            session, year
        )
        past_year_totals = await driver_history_service.get_yearly_totals_by_driver(
            session, year - 1
        )

        if not current_year_totals and not past_year_totals:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No driver history found for year {year} or {year - 1}",
            )

        driver_data = await get_drivers(session, driver_id=None, email=None)

        generator = DriverHistoryCSVGenerator(
            session, current_year_totals, past_year_totals, driver_data
        )

        csv_data, filename = await generator.generate_all_drivers_csv(year)
        csv_output = generate_csv_from_list(csv_data, header=True)

        return StreamingResponse(
            iter([csv_output]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error exporting driver history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while exporting driver history",
        ) from e


@router.get("/", response_model=list[DriverHistoryRead])
async def get_driver_history(
    driver_id: UUID,
    year: int | None = Query(default=None, ge=MIN_YEAR, le=MAX_YEAR),
    month: int | None = Query(default=None, ge=1, le=12),
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_self_driver_or_admin),
) -> list[DriverHistoryRead]:
    """
    Get monthly km totals (SUM over the mileage ledger, bucketed by drive_date).
    Rules:
    - No year, no month: return all months with activity
    - Year only: return all months for that year
    - Year + month: return specific month
    - Month without year: 400 error
    """
    if month is not None and year is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot provide month without year",
        )

    try:
        totals = await driver_history_service.get_monthly_totals(
            session, driver_id, year, month
        )

        if not totals:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No driver history found for the provided filters",
            )

        return totals

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/entries", response_model=list[DriverHistoryEntryRead])
async def get_driver_history_entries(
    driver_id: UUID,
    year: int | None = Query(default=None, ge=MIN_YEAR, le=MAX_YEAR),
    month: int | None = Query(default=None, ge=1, le=12),
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_self_driver_or_admin),
) -> list[DriverHistoryEntryRead]:
    """Individual mileage ledger entries (audit view), newest first.
    Shows exactly which deliveries, reassignments, and adjustments make up
    the driver's totals."""
    if month is not None and year is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot provide month without year",
        )

    try:
        entries = await driver_history_service.get_entries(
            session, driver_id, year, month
        )
        return [DriverHistoryEntryRead.model_validate(e) for e in entries]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.post(
    "/adjustments",
    response_model=DriverHistoryEntryRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_driver_history_adjustment(
    driver_id: UUID,
    create: DriverHistoryAdjustmentCreate,
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_admin),
) -> DriverHistoryEntryRead:
    """
    Post a signed manual mileage adjustment (admin-only).

    Appends a MANUAL_ADJUSTMENT entry to the ledger — km is a delta
    (negative to remove over-credited distance) and a note explaining the
    correction is required. Totals always reflect the sum of all entries,
    so adjustments compose with automatic credits instead of being
    overwritten by them.
    """
    if create.km == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Adjustment km must be non-zero",
        )

    if not driver_history_service.validate_year(create.drive_date.year):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"drive_date year must be between {MIN_YEAR} and {MAX_YEAR}",
        )

    if not await driver_history_service.driver_exists(session, driver_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with id {driver_id} does not exist",
        )

    entry = await driver_history_service.create_adjustment(
        session, driver_id, create.drive_date, create.km, create.note
    )
    return DriverHistoryEntryRead.model_validate(entry)

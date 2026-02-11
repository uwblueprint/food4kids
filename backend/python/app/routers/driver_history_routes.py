import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_session
from app.models.driver_history import (
    MAX_YEAR,
    MIN_YEAR,
    DriverHistoryCreate,
    DriverHistoryRead,
    DriverHistoryUpdate,
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
) -> DriverHistorySummary:
    """Get lifetime and current year KM summary for a driver"""
    try:
        return await driver_history_service.get_driver_history_summary(session, driver_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

@router.get("/{year}/export", response_class=StreamingResponse)
async def export_all_drivers_history(
    driver_id: str,
    year: int,
    session: AsyncSession = Depends(get_session),
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

        driver_history_current_year = (
            await driver_history_service.get_driver_history_by_year(session, year)
        )
        driver_history_past_year = (
            await driver_history_service.get_driver_history_by_year(session, year - 1)
        )

        if not driver_history_current_year and not driver_history_past_year:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No driver history found for year {year} or {year - 1}",
            )

        driver_data = await get_drivers(session, driver_id=None, email=None)

        generator = DriverHistoryCSVGenerator(
            session, driver_history_current_year, driver_history_past_year, driver_data
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


@router.get("/{year}", response_model=DriverHistoryRead)
async def get_driver_history(
    driver_id: UUID,
    year: int,
    session: AsyncSession = Depends(get_session),
) -> DriverHistoryRead:
    """Get a driver history by ID and year"""
    try:
        driver_history = await driver_history_service.get_driver_history_by_id_and_year(
            session, driver_id, year
        )
        if not driver_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Driver history with id {driver_id} and year {year} not found",
            )
        return DriverHistoryRead.model_validate(driver_history)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e

@router.post(
    "/{year}", response_model=DriverHistoryRead, status_code=status.HTTP_201_CREATED
)
async def create_driver_history(
    driver_id: UUID,
    year: int,
    create: DriverHistoryCreate,
    session: AsyncSession = Depends(get_session),
) -> DriverHistoryRead:
    """Create a new driver history"""

    validate_history = await driver_history_service.get_driver_history_by_id_and_year(
        session, driver_id, year
    )

    if not (MIN_YEAR <= year <= MAX_YEAR):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Year {year} is outside of the allowed range of {MIN_YEAR} to {MAX_YEAR}",
        )

    if validate_history:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Driver history with id {driver_id} and year {year} already exists and cannot be created",
        )
    created_driver_history = await driver_history_service.create_driver_history(
        session, driver_id, year, create.km
    )
    return DriverHistoryRead.model_validate(created_driver_history)


@router.patch("/{year}", response_model=DriverHistoryRead)
async def update_driver_history(
    driver_id: UUID,
    year: int,
    update: DriverHistoryUpdate,
    session: AsyncSession = Depends(get_session),
) -> DriverHistoryRead:
    """Update driver history"""
    try:
        existing_driver_history = (
            await driver_history_service.get_driver_history_by_id_and_year(
                session, driver_id, year
            )
        )
        if not existing_driver_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Driver history with id {driver_id} and year {year} not found, cannot update history not found",
            )

        updated_driver_history = (
            await driver_history_service.update_driver_history_by_id_and_year(
                session, driver_id, year, update.km
            )
        )
        logger.info(
            f"Updated driver history for driver_id={driver_id}, year={year}, new_km={update.km}"
        )
        return DriverHistoryRead.model_validate(updated_driver_history)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.delete("/{year}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver_history(
    driver_id: UUID, year: int, session: AsyncSession = Depends(get_session)
) -> None:
    """Delete driver history"""
    try:
        existing_driver_history = (
            await driver_history_service.get_driver_history_by_id_and_year(
                session, driver_id, year
            )
        )
        if not existing_driver_history:
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail=f"Driver history with id {driver_id} and year {year} not found, cannot update history not found",
            )

        await driver_history_service.delete_driver_history_by_id(
            session, driver_id, year
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e

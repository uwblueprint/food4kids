import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_session
from app.models.driver_history import (
    MAX_YEAR,
    MIN_YEAR,
    DriverHistoryCreate,
    DriverHistoryRead,
    DriverHistoryUpdate,
)
from app.services.implementations.driver_history_service import DriverHistoryService

# Initialize service
logger = logging.getLogger(__name__)
driver_history_service = DriverHistoryService(logger)

router = APIRouter(prefix="/drivers/{driver_id}/history", tags=["driver-history"])


@router.get("/", response_model=list[DriverHistoryRead])
async def get_driver_histories(
    driver_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> list[DriverHistoryRead]:
    """Get all driver histories"""
    try:
        driver_histories = await driver_history_service.get_driver_history_by_id(
            session, driver_id
        )
        if not driver_histories:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Driver history with id {driver_id} not found",
            )
        return [
            DriverHistoryRead.model_validate(driver_history)
            for driver_history in driver_histories
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
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
                session, driver_id, year
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

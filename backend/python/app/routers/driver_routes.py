import logging

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_session
from app.models.driver import DriverCreate, DriverRead, DriverUpdate
from app.services.implementations.driver_service import DriverService

# Initialize service
logger = logging.getLogger(__name__)
driver_service = DriverService(logger)

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("/", response_model=list[DriverRead])
async def get_drivers(
    session: AsyncSession = Depends(get_session),
    driver_id: UUID | None = Query(None, description="Filter by driver ID"),
    email: str | None = Query(None, description="Filter by email"),
    # _: bool = Depends(require_driver),
) -> list[DriverRead]:
    """
    Get all drivers, optionally filter by driver_id or email
    """
    if driver_id and email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot query by both driver_id and email",
        )

    try:
        if driver_id:
            driver = await driver_service.get_driver_by_id(session, driver_id)
            if not driver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Driver with id {driver_id} not found",
                )
            return [DriverRead.model_validate(driver)]

        elif email:
            driver = await driver_service.get_driver_by_email(session, email)
            if not driver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Driver with email {email} not found",
                )
            return [DriverRead.model_validate(driver)]

        else:
            drivers = await driver_service.get_drivers(session)
            return [DriverRead.model_validate(driver) for driver in drivers]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/{driver_id}", response_model=DriverRead)
async def get_driver(
    driver_id: UUID,
    session: AsyncSession = Depends(get_session),
    # _: bool = Depends(require_driver),
) -> DriverRead:
    """
    Get a single driver by ID
    """
    driver = await driver_service.get_driver_by_id(session, driver_id)
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with id {driver_id} not found",
        )
    return DriverRead.model_validate(driver)


@router.post("/", response_model=DriverRead, status_code=status.HTTP_201_CREATED)
async def create_driver(
    driver: DriverCreate,
    session: AsyncSession = Depends(get_session),
    # _: bool = Depends(require_user_or_admin),  # Temporarily disabled for testing
) -> DriverRead:
    """
    Create a new driver
    """
    try:
        created_driver = await driver_service.create_driver(session, driver)
        return DriverRead.model_validate(created_driver)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.put("/{driver_id}", response_model=DriverRead)
async def update_driver(
    driver_id: UUID,
    driver: DriverUpdate,
    session: AsyncSession = Depends(get_session),
    # _: bool = Depends(require_driver),
) -> DriverRead:
    """
    Update an existing driver
    """
    updated_driver = await driver_service.update_driver_by_id(session, driver_id, driver)
    if not updated_driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with id {driver_id} not found",
        )
    return DriverRead.model_validate(updated_driver)


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver(
    driver_id: UUID,
    session: AsyncSession = Depends(get_session),
    # _: bool = Depends(require_driver),
) -> None:
    """
    Delete a driver by ID
    """
    await driver_service.delete_driver_by_id(session, driver_id)


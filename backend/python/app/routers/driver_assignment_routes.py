import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_driver
from app.models import get_session
from app.models.driver_assignment import (
    DriverAssignmentCreate,
    DriverAssignmentRead,
    DriverAssignmentUpdate,
)
from app.services.implementations.driver_assignment_service import (
    DriverAssignmentService,
)

# Initialize service
logger = logging.getLogger(__name__)
driver_assignment_service = DriverAssignmentService(logger)

router = APIRouter(prefix="/driver-assignments", tags=["driver-assignments"])


@router.get("/", response_model=list[DriverAssignmentRead])
async def get_driver_assignments(
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
) -> list[DriverAssignmentRead]:
    """
    Get all driver assignments - Modern FastAPI approach
    """
    try:
        driver_assignments = await driver_assignment_service.get_driver_assignments(
            session
        )
        return [
            DriverAssignmentRead.model_validate(driver_assignment)
            for driver_assignment in driver_assignments
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.post(
    "/", response_model=DriverAssignmentRead, status_code=status.HTTP_201_CREATED
)
async def create_driver_assignment(
    driver_assignment: DriverAssignmentCreate,  # Auto-validated by FastAPI
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
) -> DriverAssignmentRead:
    """
    Create a new driver assignment
    """
    try:
        created_driver_assignment = (
            await driver_assignment_service.create_driver_assignment(
                session, driver_assignment
            )
        )
        return DriverAssignmentRead.model_validate(created_driver_assignment)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.patch("/{driver_assignment_id}", response_model=DriverAssignmentRead)
async def update_driver_assignment(
    driver_assignment_id: UUID,
    driver_assignment: DriverAssignmentUpdate,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
) -> DriverAssignmentRead:
    """
    Update an existing driver assignment
    """
    updated_driver_assignment = (
        await driver_assignment_service.update_driver_assignment(
            session, driver_assignment_id, driver_assignment
        )
    )
    if not updated_driver_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver assignment with id {driver_assignment_id} not found",
        )
    return DriverAssignmentRead.model_validate(updated_driver_assignment)


@router.delete("/{driver_assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver_assignment(
    driver_assignment_id: UUID,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
) -> None:
    """
    Delete a driver assignment
    """
    success = await driver_assignment_service.delete_driver_assignment(
        session, driver_assignment_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver assignment with id {driver_assignment_id} not found",
        )

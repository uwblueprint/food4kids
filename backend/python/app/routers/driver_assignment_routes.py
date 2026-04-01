from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.services import get_driver_assignment_service
from app.models import get_session
from app.models.driver_assignment import (
    DriverAssignmentCreate,
    DriverAssignmentRead,
    DriverAssignmentUpdate,
    SuggestedDriverResponse,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams, get_pagination
from app.services.implementations.driver_assignment_service import (
    DriverAssignmentService,
)

router = APIRouter(prefix="/driver-assignments", tags=["driver-assignments"])


@router.get("/", response_model=PaginatedResponse[DriverAssignmentRead])
async def get_driver_assignments(
    pagination: PaginationParams = Depends(get_pagination),
    session: AsyncSession = Depends(get_session),
    driver_assignment_service: DriverAssignmentService = Depends(
        get_driver_assignment_service
    ),
) -> PaginatedResponse[DriverAssignmentRead]:
    """
    Retrieve all driver assignments with pagination
    """
    try:
        result = await driver_assignment_service.get_driver_assignments(
            session, pagination
        )
        return PaginatedResponse.create(
            items=[DriverAssignmentRead.model_validate(da) for da in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )
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
    driver_assignment_service: DriverAssignmentService = Depends(
        get_driver_assignment_service
    ),
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
    driver_assignment_service: DriverAssignmentService = Depends(
        get_driver_assignment_service
    ),
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
    driver_assignment_service: DriverAssignmentService = Depends(
        get_driver_assignment_service
    ),
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


@router.get(
    "/suggestions",
    response_model=list[SuggestedDriverResponse],
)
async def get_suggested_driver(
    route_id: UUID,
    route_group_id: UUID,
    session: AsyncSession = Depends(get_session),
    driver_assignment_service: DriverAssignmentService = Depends(
        get_driver_assignment_service
    ),
) -> list[SuggestedDriverResponse]:
    """
    Get a suggested driver for a route on a certain day that is the last assigned to that same route
    """
    exists = await driver_assignment_service.ensure_route_and_route_group_exist(
        session, route_id, route_group_id
    )
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route or route group not found",
        )
    suggestion = await driver_assignment_service.get_suggested_driver(
        session, route_id, route_group_id
    )
    if suggestion is None:
        return []
    return [suggestion]

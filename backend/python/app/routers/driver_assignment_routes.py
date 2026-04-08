import logging
from uuid import UUID

import firebase_admin.auth
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import (
    get_access_token,
    require_admin,
    require_driver_or_admin,
)
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
from app.services.implementations.driver_service import DriverService

logger = logging.getLogger(__name__)
driver_service = DriverService(logger)

router = APIRouter(prefix="/driver-assignments", tags=["driver-assignments"])


@router.get("/", response_model=PaginatedResponse[DriverAssignmentRead])
async def get_driver_assignments(
    pagination: PaginationParams = Depends(get_pagination),
    session: AsyncSession = Depends(get_session),
    driver_assignment_service: DriverAssignmentService = Depends(
        get_driver_assignment_service
    ),
    _auth: bool = Depends(require_admin),
) -> PaginatedResponse[DriverAssignmentRead]:
    """
    Retrieve all driver assignments with pagination (admin only). Drivers should use /me.
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


@router.get("/me", response_model=list[DriverAssignmentRead])
async def get_my_driver_assignments(
    access_token: str = Depends(get_access_token),
    session: AsyncSession = Depends(get_session),
    driver_assignment_service: DriverAssignmentService = Depends(
        get_driver_assignment_service
    ),
    _auth: bool = Depends(require_driver_or_admin),
) -> list[DriverAssignmentRead]:
    """
    Retrieve driver assignments for the currently authenticated driver.
    """
    try:
        decoded_token = firebase_admin.auth.verify_id_token(
            access_token, check_revoked=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from e

    driver_id = await driver_service.get_driver_id_by_auth_id(
        session, decoded_token["uid"]
    )
    if driver_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No driver record found for current user",
        )

    try:
        driver_assignments = (
            await driver_assignment_service.get_driver_assignments_by_driver_id(
                session, driver_id
            )
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
    driver_assignment_service: DriverAssignmentService = Depends(
        get_driver_assignment_service
    ),
    _auth: bool = Depends(require_driver_or_admin),
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
    _auth: bool = Depends(require_driver_or_admin),
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
    _auth: bool = Depends(require_admin),
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
    _auth: bool = Depends(require_driver_or_admin),
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

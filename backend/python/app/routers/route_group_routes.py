from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies.auth import require_admin
from app.dependencies.services import get_location_service, get_route_group_service
from app.models import get_session
from app.models.enum import (
    DriveDaysOfWeekEnum,
    DriverAssignmentStatusEnum,
    RouteStatusEnum,
)
from app.models.route_group import (
    RouteGroup,
    RouteGroupCreate,
    RouteGroupRead,
    RouteGroupUpdate,
)
from app.services.implementations.location_service import (
    InvalidDeliveryTypeError,
    LocationService,
)
from app.services.implementations.route_group_service import RouteGroupService


def _compute_status(rg: RouteGroup) -> RouteStatusEnum:
    tz = ZoneInfo(settings.scheduler_timezone)
    now = datetime.now(tz).replace(tzinfo=None)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if rg.drive_date >= today_start:
        return RouteStatusEnum.UPCOMING
    return RouteStatusEnum.COMPLETED


router = APIRouter(prefix="/route-groups", tags=["route-groups"])


@router.get("")
async def get_route_groups(
    start_date: datetime | None = Query(
        None, description="Filter route groups from this date"
    ),
    end_date: datetime | None = Query(
        None, description="Filter route groups until this date"
    ),
    weekday: list[DriveDaysOfWeekEnum] | None = Query(
        None, description="Filter by one or more weekdays"
    ),
    delivery_type: list[str] | None = Query(
        None, description="Filter by one or more delivery types"
    ),
    route_status: list[RouteStatusEnum] | None = Query(
        None, description="Filter by one or more route statuses"
    ),
    driver_assignment_status: list[DriverAssignmentStatusEnum] | None = Query(
        None, description="Filter by one or more driver assignment statuses"
    ),
    include_routes: bool = Query(False, description="Include routes in the response"),
    session: AsyncSession = Depends(get_session),
    route_group_service: RouteGroupService = Depends(get_route_group_service),
    location_service: LocationService = Depends(get_location_service),
    _auth: bool = Depends(require_admin),
) -> list[RouteGroupRead]:
    """
    Retrieve all route groups, optionally filtered by date range, weekday, delivery type, route status, and driver assignment status.
    Can include associated routes in the response.
    """
    try:
        if delivery_type:
            await location_service.validate_delivery_types(session, delivery_type)
        return await route_group_service.get_route_groups(
            session,
            start_date,
            end_date,
            weekday,
            delivery_type,
            route_status,
            driver_assignment_status,
            include_routes,
        )
    except InvalidDeliveryTypeError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(ve)
        ) from ve
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.post("", response_model=RouteGroupRead, status_code=status.HTTP_201_CREATED)
async def create_route_group(
    route_group: RouteGroupCreate,
    session: AsyncSession = Depends(get_session),
    route_group_service: RouteGroupService = Depends(get_route_group_service),
    _auth: bool = Depends(require_admin),
) -> RouteGroupRead:
    """
    Create a new route group
    """
    try:
        created_route_group = await route_group_service.create_route_group(
            session, route_group
        )
        return RouteGroupRead(
            route_group_id=created_route_group.route_group_id,
            name=created_route_group.name,
            notes=created_route_group.notes,
            drive_date=created_route_group.drive_date,
            created_at=created_route_group.created_at,
            updated_at=created_route_group.updated_at,
            num_routes=created_route_group.num_routes,
            status=_compute_status(created_route_group),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.patch("/{route_group_id}", response_model=RouteGroupRead)
async def update_route_group(
    route_group_id: UUID,
    route_group: RouteGroupUpdate,
    session: AsyncSession = Depends(get_session),
    route_group_service: RouteGroupService = Depends(get_route_group_service),
    _auth: bool = Depends(require_admin),
) -> RouteGroupRead:
    """
    Update an existing route group
    """
    try:
        updated_route_group = await route_group_service.update_route_group(
            session, route_group_id, route_group
        )
        if not updated_route_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RouteGroup with id {route_group_id} not found",
            )
        return RouteGroupRead(
            route_group_id=updated_route_group.route_group_id,
            name=updated_route_group.name,
            notes=updated_route_group.notes,
            drive_date=updated_route_group.drive_date,
            created_at=updated_route_group.created_at,
            updated_at=updated_route_group.updated_at,
            num_routes=updated_route_group.num_routes,
            status=_compute_status(updated_route_group),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.post(
    "/{route_group_id}/duplicate",
    response_model=RouteGroupRead,
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_route_group(
    route_group_id: UUID,
    session: AsyncSession = Depends(get_session),
    route_group_service: RouteGroupService = Depends(get_route_group_service),
    _auth: bool = Depends(require_admin),
) -> RouteGroupRead:
    """
    Duplicate a route group and its routes/stops for a new planning cycle.
    """
    try:
        duplicated_route_group = await route_group_service.duplicate_route_group(
            session, route_group_id
        )
        if not duplicated_route_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RouteGroup with id {route_group_id} not found",
            )
        return RouteGroupRead(
            route_group_id=duplicated_route_group.route_group_id,
            name=duplicated_route_group.name,
            notes=duplicated_route_group.notes,
            drive_date=duplicated_route_group.drive_date,
            created_at=duplicated_route_group.created_at,
            updated_at=duplicated_route_group.updated_at,
            num_routes=duplicated_route_group.num_routes,
            status=_compute_status(duplicated_route_group),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.delete("/{route_group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route_group(
    route_group_id: UUID,
    session: AsyncSession = Depends(get_session),
    route_group_service: RouteGroupService = Depends(get_route_group_service),
    _auth: bool = Depends(require_admin),
) -> None:
    """
    Delete a route group and all its route group memberships
    """
    try:
        success = await route_group_service.delete_route_group(session, route_group_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RouteGroup with id {route_group_id} not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e

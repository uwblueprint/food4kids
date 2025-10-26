import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_session
from app.models.route_group import RouteGroupCreate, RouteGroupRead, RouteGroupUpdate
from app.services.implementations.route_group_service import RouteGroupService

logger = logging.getLogger(__name__)
route_group_service = RouteGroupService(logger)

router = APIRouter(prefix="/route-groups", tags=["route-groups"])


@router.get("", response_model=list[RouteGroupRead])
async def get_route_groups(
    start_date: Optional[datetime] = Query(None, description="Filter route groups from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter route groups until this date"),
    include_routes: bool = Query(False, description="Include routes in the response"),
    session: AsyncSession = Depends(get_session),
) -> list[RouteGroupRead]:
    """
    Get route groups with optional date filtering and route inclusion
    """
    route_groups = await route_group_service.get_route_groups(
        session, start_date, end_date, include_routes
    )
    return [
        RouteGroupRead(
            route_group_id=rg.route_group_id,
            name=rg.name,
            notes=rg.notes,
            drive_date=rg.drive_date,
            num_routes=len(rg.route_group_memberships) if hasattr(rg, 'route_group_memberships') else 0
        ) for rg in route_groups
    ]


@router.post("", response_model=RouteGroupRead, status_code=status.HTTP_201_CREATED)
async def create_route_group(
    route_group: RouteGroupCreate,
    session: AsyncSession = Depends(get_session),
) -> RouteGroupRead:
    """
    Create a new route group
    """
    new_route_group = await route_group_service.create_route_group(session, route_group)
    return RouteGroupRead(
        route_group_id=new_route_group.route_group_id,
        name=new_route_group.name,
        notes=new_route_group.notes,
        drive_date=new_route_group.drive_date,
        num_routes=0  # New route groups start with 0 routes
    )


@router.patch("/{route_group_id}", response_model=RouteGroupRead)
async def update_route_group(
    route_group_id: UUID,
    route_group: RouteGroupUpdate,
    session: AsyncSession = Depends(get_session),
) -> RouteGroupRead:
    """
    Update an existing route group
    """
    updated_route_group = await route_group_service.update_route_group(
        session, route_group_id, route_group
    )
    if not updated_route_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RouteGroup with id {route_group_id} not found",
        )
    return RouteGroupRead.model_validate(updated_route_group)


@router.delete("/{route_group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route_group(
    route_group_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    """
    Delete a route group and all its route group memberships
    """
    success = await route_group_service.delete_route_group(session, route_group_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RouteGroup with id {route_group_id} not found",
        )

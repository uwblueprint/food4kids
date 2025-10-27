import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.services import get_route_group_service
from app.models import get_session
from app.models.route_group import RouteGroupCreate, RouteGroupRead, RouteGroupUpdate
from app.services.implementations.route_group_service import RouteGroupService

router = APIRouter(prefix="/route-groups", tags=["route-groups"])


@router.get("", response_model=list[RouteGroupRead])
async def get_route_groups(
    start_date: Optional[datetime] = Query(None, description="Filter route groups from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter route groups until this date"),
    include_routes: bool = Query(False, description="Include routes in the response"),
    session: AsyncSession = Depends(get_session),
    route_group_service: RouteGroupService = Depends(get_route_group_service),
) -> list[RouteGroupRead]:
    """
    Get route groups with optional date filtering and route inclusion
    """
    route_groups = await route_group_service.get_route_groups(
        session, start_date, end_date, include_routes
    )

    result = []
    for rg in route_groups:
        route_group_data = {
            "route_group_id": rg.route_group_id,
            "name": rg.name,
            "notes": rg.notes,
            "drive_date": rg.drive_date,
            "num_routes": len(rg.route_group_memberships) if hasattr(rg, 'route_group_memberships') else 0
        }

        # Include routes if requested
        if include_routes and hasattr(rg, 'route_group_memberships'):
            routes = []
            for membership in rg.route_group_memberships:
                if hasattr(membership, 'route') and membership.route:
                    routes.append({
                        "route_id": membership.route.route_id,
                        "name": getattr(membership.route, 'name', 'Unknown Route'),
                        "description": getattr(membership.route, 'description', ''),
                    })
            route_group_data["routes"] = routes

        result.append(RouteGroupRead(**route_group_data))

    return result


@router.post("", response_model=RouteGroupRead, status_code=status.HTTP_201_CREATED)
async def create_route_group(
    route_group: RouteGroupCreate,
    session: AsyncSession = Depends(get_session),
    route_group_service: RouteGroupService = Depends(get_route_group_service),
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
    route_group_service: RouteGroupService = Depends(get_route_group_service),
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

    # Build response manually to avoid accessing relationships that might not be loaded
    route_group_data = {
        "route_group_id": updated_route_group.route_group_id,
        "name": updated_route_group.name,
        "notes": updated_route_group.notes,
        "drive_date": updated_route_group.drive_date,
        "num_routes": 0,  # Default to 0 since we don't load relationships in update
        "routes": None
    }

    return RouteGroupRead(**route_group_data)


@router.delete("/{route_group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route_group(
    route_group_id: UUID,
    session: AsyncSession = Depends(get_session),
    route_group_service: RouteGroupService = Depends(get_route_group_service),
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
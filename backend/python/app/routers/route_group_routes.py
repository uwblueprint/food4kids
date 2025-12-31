from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.services import get_route_group_service
from app.models import get_session
from app.models.route_group import RouteGroupCreate, RouteGroupRead, RouteGroupUpdate
from app.services.implementations.route_group_service import RouteGroupService

router = APIRouter(prefix="/route-groups", tags=["route-groups"])


@router.get("")
async def get_route_groups(
    start_date: datetime | None = Query(
        None, description="Filter route groups from this date"
    ),
    end_date: datetime | None = Query(
        None, description="Filter route groups until this date"
    ),
    include_routes: bool = Query(False, description="Include routes in the response"),
    session: AsyncSession = Depends(get_session),
    route_group_service: RouteGroupService = Depends(get_route_group_service),
) -> list[dict]:
    """
    Retrieve all route groups, optionally filtered by date range.
    Can include associated routes in the response.
    """
    try:
        route_groups = await route_group_service.get_route_groups(
            session, start_date, end_date, include_routes
        )
        result = []
        for route_group in route_groups:
            data = RouteGroupRead.model_validate(route_group).model_dump()
            membership_count = len(route_group.route_group_memberships)
            data["num_routes"] = membership_count
            if include_routes:
                data["routes"] = [
                    {
                        "route_id": membership.route.route_id
                        if membership.route
                        else None,
                        "name": membership.route.name
                        if membership.route
                        else "No route",
                        "notes": membership.route.notes
                        if membership.route
                        else "No notes",
                        "length": membership.route.length if membership.route else 0,
                    }
                    for membership in route_group.route_group_memberships
                ]
            else:
                data["routes"] = []
            result.append(data)

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.post("", response_model=RouteGroupRead, status_code=status.HTTP_201_CREATED)
async def create_route_group(
    route_group: RouteGroupCreate,
    session: AsyncSession = Depends(get_session),
    route_group_service: RouteGroupService = Depends(get_route_group_service),
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
            num_routes=0,
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
        return RouteGroupRead.model_validate(updated_route_group)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.delete("/{route_group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route_group(
    route_group_id: UUID,
    session: AsyncSession = Depends(get_session),
    route_group_service: RouteGroupService = Depends(get_route_group_service),
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e

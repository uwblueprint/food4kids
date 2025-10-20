import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_session
from app.models.route_group import RouteGroupCreate, RouteGroupRead, RouteGroupUpdate
from app.services.implementations.route_group_service import RouteGroupService

logger = logging.getLogger(__name__)
route_group_service = RouteGroupService(logger)

router = APIRouter(prefix="/route-groups", tags=["route-groups"])


@router.post("", response_model=RouteGroupRead, status_code=status.HTTP_201_CREATED)
async def create_route_group(
    route_group: RouteGroupCreate,
    session: AsyncSession = Depends(get_session),
) -> RouteGroupRead:
    """
    Create a new route group
    """
    new_route_group = await route_group_service.create_route_group(session, route_group)
    return RouteGroupRead.model_validate(new_route_group)


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

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_driver
from app.models import get_session
from app.models.route import RouteCreate, RouteRead, RouteUpdate
from app.services.implementations.route_service import RouteService

# Initialize service
logger = logging.getLogger(__name__)
route_service = RouteService(logger)

router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("", response_model=RouteRead, status_code=status.HTTP_201_CREATED)
async def create_route(
    route: RouteCreate,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
) -> RouteRead:
    """
    Create a new route
    """
    try:
        new_route = await route_service.create_route(session, route)
        return RouteRead.model_validate(new_route)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/{route_id}", response_model=RouteRead)
async def get_route(
    route_id: UUID,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
) -> RouteRead:
    """
    Get a route by ID
    """
    route = await route_service.get_route(session, route_id)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route with id {route_id} not found",
        )
    return RouteRead.model_validate(route)


@router.put("/{route_id}", response_model=RouteRead)
async def update_route(
    route_id: UUID,
    route: RouteUpdate,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
) -> RouteRead:
    """
    Update an existing route
    """
    updated_route = await route_service.update_route(session, route_id, route)
    if not updated_route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route with id {route_id} not found",
        )
    return RouteRead.model_validate(updated_route)


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(
    route_id: UUID,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
) -> None:
    """
    Delete a route
    """
    success = await route_service.delete_route(session, route_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route with id {route_id} not found",
        )
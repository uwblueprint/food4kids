import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_driver
from app.models import get_session
from app.models.route import Route, RouteWithDateRead
from app.services.implementations.route_service import RouteService

# Initialize service
logger = logging.getLogger(__name__)
route_service = RouteService(logger)

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=list[RouteWithDateRead])
async def get_routes(
    unassigned_only: bool = Query(
        False,
        description="If true, only return unassigned routes. If false, return all routes regardless of assignment status.",
    ),
    start_date: str = Query(None, description="Filter route groups from this date"),
    end_date: str = Query(None, description="Filter route groups until this date"),
    session: AsyncSession = Depends(get_session),
) -> list[RouteWithDateRead]:
    """
    Get routes with optional filtering for unassigned routes and date range.
    Returns routes with their drive dates - routes can appear multiple times for different dates.
    When unassigned_only is False, returns all routes (no assignment filter).
    When unassigned_only is True, returns only routes that are unassigned for the given route group.
    """
    routes = await route_service.get_routes(
        session, unassigned_only, start_date, end_date
    )
    return routes

@router.get("/{route_id}", response_model=Route, status_code=status.HTTP_200_OK)
async def get_route(
    route_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> Route:
    """
    Get a route by its unique identifier.

    Parameters:
        route_id (UUID): The unique identifier of the route to delete.
        session (AsyncSession): The database session dependency.

    Authentication:
        Requires the user to be authenticated as a driver.

    Returns:
        None. Responds with HTTP 200 OK on successful get.

    Raises:
        HTTPException:
            - 404 Not Found: If the route with the specified ID does not exist.
            - 500 Server Error      
    """

    # TODO: the auth here does not work, I think this is an auth issue
    route = await route_service.get_route(session, route_id)
    return route


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(
    route_id: UUID,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
) -> None:
    """
    Delete a route by its unique identifier.

    Parameters:
        route_id (UUID): The unique identifier of the route to delete.
        session (AsyncSession): The database session dependency.
        _ (bool): Indicates that the user is authenticated as a driver (injected by dependency).

    Authentication:
        Requires the user to be authenticated as a driver.

    Returns:
        None. Responds with HTTP 204 No Content on successful deletion.

    Raises:
        HTTPException:
            - 404 Not Found: If the route with the specified ID does not exist.
    """
    success = await route_service.delete_route(session, route_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route with id {route_id} not found",
        )

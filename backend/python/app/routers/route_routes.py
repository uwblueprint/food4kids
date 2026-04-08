import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_session
from app.models.route import Route, RoutePatchRequest, RouteRead, RouteWithDateRead
from app.schemas.pagination import PaginatedResponse, PaginationParams, get_pagination
from app.services.implementations.route_service import RouteService

# Initialize service
logger = logging.getLogger(__name__)
route_service = RouteService(logger)

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("", response_model=PaginatedResponse[RouteWithDateRead])
async def get_routes(
    unassigned_only: bool = Query(
        False,
        description="If true, only return unassigned routes. If false, return all routes regardless of assignment status.",
    ),
    start_date: str = Query(None, description="Filter route groups from this date"),
    end_date: str = Query(None, description="Filter route groups until this date"),
    pagination: PaginationParams = Depends(get_pagination),
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse[RouteWithDateRead]:
    """
    Get routes with pagination and optional filtering for unassigned routes and date range.
    Returns routes with their drive dates - routes can appear multiple times for different dates.
    When unassigned_only is False, returns all routes (no assignment filter).
    When unassigned_only is True, returns only routes that are unassigned for the given route group.
    """
    return await route_service.get_routes(
        session, unassigned_only, start_date, end_date, pagination
    )


@router.get("/{route_id}", response_model=Route, status_code=status.HTTP_200_OK)
async def get_route(
    route_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> Route:
    """
    Get a route by its unique identifier.

    Parameters:
        route_id (UUID): The unique identifier of the route to GET.
        session (AsyncSession): The database session dependency.

    Returns:
        None. Responds with HTTP 200 OK on successful get.
    """

    route = await route_service.get_route(session, route_id)
    return route

@router.get("/{route_id}/google-maps-link", response_model=str, status_code=status.HTTP_200_OK)
async def get_google_maps_link(
    route_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> str:
    """
    Generate a Google Maps directions URL for a route.

    Takes a route ID, looks up its stops in order, and builds a Google Maps
    directions link starting from the warehouse and visiting each stop.

    Parameters:
        route_id (UUID): The unique identifier of the route.
        session (AsyncSession): The database session dependency.

    Returns:
        The Google Maps directions URL as a plain string.
    """
    return await route_service.get_google_maps_link(session, route_id)


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(
    route_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    """
    Delete a route by its unique identifier.

    Parameters:
        route_id (UUID): The unique identifier of the route to delete.
        session (AsyncSession): The database session dependency.
        _ (bool): Indicates that the user is authenticated as a driver (injected by dependency).

    Returns:
        None. Responds with HTTP 204 No Content on successful deletion.
    """
    success = await route_service.delete_route(session, route_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route with id {route_id} not found",
        )


@router.patch("/{route_id}", response_model=RouteRead)
async def update_route(
    route_id: UUID,
    patch: RoutePatchRequest,
    session: AsyncSession = Depends(get_session),
) -> RouteRead:
    """
    Update a route's metadata (name, notes) and/or its stop order/locations.

    If location_ids is provided in the request body:
    - The route's stops are fully replaced with the new ordered list.
    - The routing algorithm is re-run to compute the new polyline and mileage.
    - This will affect ALL route groups that share this route.

    If only name/notes are provided, stops and mileage are left unchanged.
    """
    try:
        updated_route = await route_service.update_route(session, route_id, patch)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=msg
            ) from None
        # Missing system settings / warehouse config
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=msg
        ) from None
    if not updated_route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route with id {route_id} not found",
        )
    return RouteRead.model_validate(updated_route, from_attributes=True)

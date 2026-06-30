import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import (
    require_admin,
    require_route_assigned_or_admin,
    resolve_route_list_driver_filter,
)
from app.models import get_session
from app.models.route import (
    RouteDetailRead,
    RoutePatchRequest,
    RouteRead,
    RouteWithDateRead,
    SuggestedDriverResponse,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams, get_pagination
from app.services.implementations.route_service import (
    RouteService,
    RoutingConfigurationError,
)

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
    driver_id: UUID | None = Depends(resolve_route_list_driver_filter),
) -> PaginatedResponse[RouteWithDateRead]:
    """
    Get routes with pagination and optional filtering for unassigned routes and date range.
    Returns routes with their drive dates - routes can appear multiple times for different dates.
    When unassigned_only is False, returns all routes (no assignment filter).
    When unassigned_only is True, returns only routes that are unassigned for the given route group.

    Requires a driver or admin caller.
    Admins may scope to any driver via driver_id (or omit it for all routes).
    Drivers are always scoped to their own routes: omitting driver_id returns
    their own routes, and requesting another driver's is rejected.
    """
    if unassigned_only and driver_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot combine unassigned_only with a driver scope: "
            "unassigned routes have no driver. (Drivers are always scoped to "
            "themselves, so they cannot list unassigned routes.)",
        )
    return await route_service.get_routes(
        session, unassigned_only, start_date, end_date, pagination, driver_id
    )


@router.get(
    "/{route_id}", response_model=RouteDetailRead, status_code=status.HTTP_200_OK
)
async def get_route(
    route_id: UUID,
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_route_assigned_or_admin),
) -> RouteDetailRead:
    """
    Get a route by its unique identifier, with its ordered stops embedded.

    Each stop carries its sequence #, address, contact name, phone (+ secondary),
    box count, and a note_chain_id reference. Stops are sourced live from
    Location for upcoming routes and from frozen route_stop_snapshots for past
    routes. Notes are not embedded: fetch them via GET /note-chains/{id}/notes.

    Parameters:
        route_id (UUID): The unique identifier of the route to GET.
        session (AsyncSession): The database session dependency.

    Returns:
        The route with its ordered stops. Responds with HTTP 200 OK on success.
    """

    route = await route_service.get_route(session, route_id)
    return route


@router.get(
    "/{route_id}/google-maps-link", response_model=str, status_code=status.HTTP_200_OK
)
async def get_google_maps_link(
    route_id: UUID,
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_route_assigned_or_admin),
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


@router.get(
    "/{route_id}/suggested-driver",
    response_model=SuggestedDriverResponse | None,
    status_code=status.HTTP_200_OK,
)
async def get_suggested_driver(
    route_id: UUID,
    route_group_id: UUID = Query(
        ..., description="Route group the route is being assigned within"
    ),
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_admin),
) -> SuggestedDriverResponse | None:
    """
    Suggest a driver to assign to a route: the active driver most familiar
    with the route's locations (by past completed deliveries), excluding
    drivers already assigned within the given route group.

    Parameters:
        route_id (UUID): The route to suggest a driver for.
        route_group_id (UUID): The route group the assignment is within.
        session (AsyncSession): The database session dependency.

    Returns:
        The suggested driver, or null if there's no candidate.
    """
    return await route_service.get_suggested_driver(session, route_id, route_group_id)


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(
    route_id: UUID,
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_admin),
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
    _auth: bool = Depends(require_admin),
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
    except RoutingConfigurationError as e:
        # Server isn't configured for routing (missing settings/warehouse coords)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        ) from None
    except ValueError as e:
        # Bad client input (e.g. unknown location_ids)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from None
    if not updated_route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Route with id {route_id} not found",
        )
    return RouteRead.model_validate(updated_route, from_attributes=True)

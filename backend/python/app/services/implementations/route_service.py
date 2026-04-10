import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, exists
from sqlalchemy import select as sql_select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.models.driver_assignment import DriverAssignment
from app.models.location import Location
from app.models.route import Route, RoutePatchRequest, RouteWithDateRead
from app.models.route_group import RouteGroup
from app.models.route_group_membership import RouteGroupMembership
from app.models.route_stop import RouteStop
from app.models.system_settings import SystemSettings
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.utilities.google_maps_link import build_google_maps_directions_url
from app.utilities.pagination import paginate_query
from app.utilities.routes_utils import fetch_route_polyline


class RouteService:
    """
    Service class for handling route-related operations.

    This class provides methods to manage Route entities, such as deleting routes by their ID.
    While currently only the delete operation is implemented, this class is intended to be extended
    with additional route-related operations in the future.
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_routes(
        self,
        session: AsyncSession,
        unassigned_only: bool = False,
        start_date: str | None = None,
        end_date: str | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResponse[RouteWithDateRead]:
        """
        Get routes with optional filtering for unassigned routes and date range.
        Returns routes with their drive dates - routes can appear multiple times for different dates.
        When unassigned_only is False, returns all routes (no assignment filter).
        When unassigned_only is True, returns only routes that are unassigned for the given route group.
        """
        statement = (
            select(
                Route,
                RouteGroup.route_group_id,
                RouteGroup.drive_date,
            )
            .join(RouteGroupMembership, Route.route_id == RouteGroupMembership.route_id)  # type: ignore[arg-type]
            .join(
                RouteGroup,
                RouteGroupMembership.route_group_id == RouteGroup.route_group_id,  # type: ignore[arg-type]
            )
        )

        # Parse and filter by date range
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            statement = statement.where(RouteGroup.drive_date >= start_dt)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            statement = statement.where(RouteGroup.drive_date <= end_dt)

        # Filter for unassigned routes only
        if unassigned_only:
            statement = statement.where(
                ~exists(
                    sql_select(1)
                    .select_from(DriverAssignment)
                    .where(
                        and_(
                            DriverAssignment.route_id == Route.route_id,  # type: ignore[arg-type]
                            DriverAssignment.route_group_id
                            == RouteGroup.route_group_id,  # type: ignore[arg-type]
                        )
                    )
                )
            )

        statement = statement.order_by(RouteGroup.drive_date, Route.name)  # type: ignore[arg-type]

        if pagination is None:
            pagination = PaginationParams()

        result, total = await paginate_query(session, statement, pagination)
        rows = result.all()

        items = [
            RouteWithDateRead(
                route_id=row.Route.route_id,
                name=row.Route.name,
                notes=row.Route.notes,
                length=row.Route.length,
                drive_date=row.drive_date,
            )
            for row in rows
        ]

        return PaginatedResponse.create(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def get_route(self, session: AsyncSession, route_id: UUID) -> Route:
        """Get route by ID"""
        try:
            statement = select(Route).where(Route.route_id == route_id)
            result = await session.execute(statement)
            route = result.scalars().first()

        except Exception as error:
            self.logger.exception("Failed to get route " + str(route_id))
            await session.rollback()
            raise HTTPException(
                status_code=500, detail="Failed to retrieve route."
            ) from error

        if not route:
            raise HTTPException(
                status_code=404, detail=f"Route with id {route_id} not found"
            )

        return route

    async def delete_route(self, session: AsyncSession, route_id: UUID) -> bool:
        """Delete route by ID"""
        try:
            statement = select(Route).where(Route.route_id == route_id)
            result = await session.execute(statement)
            route = result.scalars().first()

            if not route:
                self.logger.error(f"Route with id {route_id} not found")
                return False

            await session.delete(route)
            await session.commit()

            return True
        except Exception as error:
            self.logger.error(f"Failed to delete route {route_id}: {error!s}")
            await session.rollback()
            raise error

    async def update_route(
        self,
        session: AsyncSession,
        route_id: UUID,
        patch: RoutePatchRequest,
    ) -> Route | None:
        """Update a route's metadata and/or stops.

        If location_ids are provided:
        - Existing route stops are deleted and replaced with the new ordered list.
        - fetch_route_polyline is called to get the new encoded polyline + distance.
        - Route.length and Route.encoded_polyline are updated accordingly.

        Metadata fields (name, notes) are updated independently if provided.

        Since routes can be shared across multiple route groups, all route groups
        that reference this route will automatically see the updated version.

        Args:
            session: Database session
            route_id: ID of the route to update
            patch: Patch request body (RoutePatchRequest)

        Returns:
            The updated Route, or None if not found.
        """

        try:
            # Fetch the route
            result = await session.execute(
                select(Route).where(Route.route_id == route_id)
            )
            route = result.scalars().first()

            if not route:
                self.logger.error(f"Route with id {route_id} not found for update")
                return None

            # Update metadata fields if provided
            if patch.name is not None:
                route.name = patch.name
            if patch.notes is not None:
                route.notes = patch.notes

            # Update stops + re-run routing if location_ids provided
            if patch.location_ids is not None:
                location_results = await session.execute(
                    select(Location).where(
                        col(Location.location_id).in_(patch.location_ids)
                    )
                )
                locations_by_id = {
                    loc.location_id: loc for loc in location_results.scalars().all()
                }

                # Validate all requested location IDs exist
                missing = [
                    str(loc_id)
                    for loc_id in patch.location_ids
                    if loc_id not in locations_by_id
                ]
                if missing:
                    raise ValueError(f"Location IDs not found: {', '.join(missing)}")

                # Preserve the caller-specified order
                ordered_locations = [
                    locations_by_id[loc_id] for loc_id in patch.location_ids
                ]

                # Fetch warehouse coordinates from system_settings
                settings_result = await session.execute(select(SystemSettings))
                system_settings = settings_result.scalars().first()

                if not system_settings:
                    raise ValueError(
                        "System settings not found - cannot fetch warehouse coordinates for routing"
                    )
                if (
                    system_settings.warehouse_latitude is None
                    or system_settings.warehouse_longitude is None
                ):
                    raise ValueError(
                        "Warehouse coordinates not set in system settings - cannot perform routing"
                    )

                warehouse_lat = system_settings.warehouse_latitude
                warehouse_lon = system_settings.warehouse_longitude

                # Call fetch route polyline for new polyline + distance
                encoded_polyline, distance_km = await fetch_route_polyline(
                    locations=ordered_locations,
                    warehouse_lat=warehouse_lat,
                    warehouse_lon=warehouse_lon,
                    ends_at_warehouse=route.ends_at_warehouse,
                )

                # Delete existing route stops
                existing_stops_result = await session.execute(
                    select(RouteStop).where(RouteStop.route_id == route_id)
                )
                for stop in existing_stops_result.scalars().all():
                    await session.delete(stop)

                # Create new route stops in the given order
                for stop_number, location in enumerate(ordered_locations, start=1):
                    new_stop = RouteStop(
                        route_id=route_id,
                        location_id=location.location_id,
                        stop_number=stop_number,
                    )
                    session.add(new_stop)

                # Update route polyline and mileage
                route.encoded_polyline = encoded_polyline
                route.polyline_updated_at = datetime.now(timezone.utc)
                route.length = distance_km

            # Persist
            session.add(route)
            await session.commit()
            await session.refresh(route)

            return route
        except Exception as error:
            self.logger.error(f"Failed to update route {route_id}: {error!s}")
            await session.rollback()
            raise error
    async def get_google_maps_link(
        self, session: AsyncSession, route_id: UUID
    ) -> str:
        """Generate a Google Maps directions URL for a route.

        Fetches the route's stops (ordered by stop_number), joins each stop
        to its location to get the address/coordinates, retrieves the
        warehouse origin from SystemSettings, and builds the URL.

        Returns:
            The Google Maps directions URL string.

        Raises:
            HTTPException 404: If the route or system settings are not found.
            HTTPException 422: If a stop is missing both address and coordinates.
        """
        # 1. Fetch route stops with their locations, ordered by stop_number
        statement = (
            select(RouteStop, Location)
            .join(Location, RouteStop.location_id == Location.location_id)  # type: ignore[arg-type]
            .where(RouteStop.route_id == route_id)
            .order_by(RouteStop.stop_number)  # type: ignore[arg-type]
        )
        result = await session.execute(statement)
        rows = result.all()

        if not rows:
            # Verify the route exists (raises 404 if not found)
            await self.get_route(session, route_id)
            # Route exists but has no stops
            raise HTTPException(
                status_code=422,
                detail=f"Route {route_id} has no stops.",
            )

        # 2. Fetch warehouse coordinates from SystemSettings
        settings_result = await session.execute(select(SystemSettings).limit(1))
        system_settings = settings_result.scalars().first()

        if not system_settings:
            raise HTTPException(
                status_code=404,
                detail="System settings not found.",
            )
        if (
            system_settings.warehouse_latitude is None
            or system_settings.warehouse_longitude is None
        ):
            raise HTTPException(
                status_code=422,
                detail="Warehouse coordinates are not configured in system settings.",
            )

        # 3. Extract the ordered list of Location objects
        locations: list[Location] = [location for _, location in rows]

        # 4. Generate the URL
        try:
            url = build_google_maps_directions_url(
                locations=locations,
                warehouse_lat=system_settings.warehouse_latitude,
                warehouse_lon=system_settings.warehouse_longitude,
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

        return url

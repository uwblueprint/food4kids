import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.models.driver import Driver
from app.models.location import Location
from app.models.route import (
    Route,
    RoutePatchRequest,
    RouteWithDateRead,
    SuggestedDriverRead,
)
from app.models.route_group import RouteGroup
from app.models.route_snapshot import RouteSnapshot
from app.models.route_stop import RouteStop
from app.models.system_settings import SystemSettings
from app.models.user import User
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.utilities.google_maps_link import build_google_maps_directions_url
from app.utilities.pagination import paginate_query
from app.utilities.routes_utils import fetch_route_polyline


class RoutingConfigurationError(Exception):
    """Raised when routing can't run because the server isn't configured
    (e.g. missing system settings / warehouse coordinates). Distinct from
    bad client input so the API can map it to 503 rather than 400.
    """


class RouteService:
    """
    Service class for handling route-related operations.
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

        unassigned_only filters to routes with no driver_id. The date range
        filters on the route's RouteGroup.drive_date.
        """
        statement = select(Route, RouteGroup.drive_date).join(
            RouteGroup,
            RouteGroup.route_group_id == Route.route_group_id,  # type: ignore[arg-type]
        )

        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            statement = statement.where(RouteGroup.drive_date >= start_dt)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            statement = statement.where(RouteGroup.drive_date <= end_dt)

        if unassigned_only:
            statement = statement.where(col(Route.driver_id).is_(None))

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

        Metadata fields (name, notes, driver_id, start_time) are updated
        independently if provided.

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
            # driver_id is nullable, so an explicit null means "unassign". Use
            # model_fields_set to tell an explicit null apart from an omitted
            # field (both are None on the model).
            if "driver_id" in patch.model_fields_set:
                route.driver_id = patch.driver_id
            if patch.start_time is not None:
                route.start_time = patch.start_time

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
                    raise RoutingConfigurationError(
                        "System settings not found - cannot fetch warehouse coordinates for routing"
                    )
                if (
                    system_settings.warehouse_latitude is None
                    or system_settings.warehouse_longitude is None
                ):
                    raise RoutingConfigurationError(
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

                # Flush the deletes before inserting replacements: route_stops
                # has UNIQUE(route_id, stop_number) and UNIQUE(route_id,
                # location_id), and SQLAlchemy's unit of work may otherwise
                # emit the INSERTs before the DELETEs, transiently violating
                # the constraints even though the end state is valid.
                await session.flush()

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

    async def get_google_maps_link(self, session: AsyncSession, route_id: UUID) -> str:
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

    async def get_suggested_drivers_for_route(
        self,
        session: AsyncSession,
        route_id: UUID,
        limit: int = 5,
    ) -> list[SuggestedDriverRead]:
        """Suggest drivers by location familiarity: rank active drivers by
        their count of past completed (frozen) deliveries to this route's
        locations, and return the top `limit`.
        """
        # Subquery: location_ids that make up the target route.
        target_locations = (
            select(RouteStop.location_id)
            .where(RouteStop.route_id == route_id)
            .subquery()
        )

        # Past completed routes' driver_id x delivery count to those locations.
        statement = (
            select(
                Route.driver_id,
                User.name,
                func.count().label("deliveries"),
            )
            .join(RouteStop, RouteStop.route_id == Route.route_id)  # type: ignore[arg-type]
            .join(RouteSnapshot, RouteSnapshot.route_id == Route.route_id)  # type: ignore[arg-type]
            .join(Driver, Driver.driver_id == Route.driver_id)  # type: ignore[arg-type]
            .join(User, User.user_id == Driver.user_id)  # type: ignore[arg-type]
            .where(
                col(RouteStop.location_id).in_(select(target_locations.c.location_id))
            )
            .where(col(Route.driver_id).isnot(None))
            .where(Route.route_id != route_id)
            .where(col(Driver.active).is_(True))
            .group_by(col(Route.driver_id), User.name)
            .order_by(func.count().desc())
            .limit(limit)
        )

        result = await session.execute(statement)
        return [
            SuggestedDriverRead(
                driver_id=row.driver_id,
                name=row.name,
                score=row.deliveries,
            )
            for row in result.all()
        ]

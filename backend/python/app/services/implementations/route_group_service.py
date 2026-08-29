import logging
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import and_, case, distinct, exists, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from app.config import settings
from app.models.enum import (
    DriveDaysOfWeekEnum,
    DriverAssignmentStatusEnum,
    RouteStatusEnum,
)
from app.models.location import Location
from app.models.route import Route
from app.models.route_group import (
    RouteGroup,
    RouteGroupCreate,
    RouteGroupDuplicate,
    RouteGroupRead,
    RouteGroupUpdate,
    RouteReadSummary,
)
from app.models.route_snapshot import RouteSnapshot
from app.models.route_stop import RouteStop
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.utilities.boxes import box_count_expr, resolve_children_per_box
from app.utilities.pagination import paginate_query

ROUTE_GROUP_COPY_PREFIX = "Copy of "
ROUTE_GROUP_NAME_MAX_LENGTH = 255


class FrozenRouteGroupError(Exception):
    """Raised when an edit would move an already-frozen group's drive date.

    Freezing snapshots a route as delivered, and the group's drive_date is the
    date that record is filed under. Moving it forward would leave the snapshot
    behind: the group would read "Upcoming" while still counting as driven, and
    the freeze job (which only scans due, un-frozen routes) would never revisit
    it. Correcting a frozen group's date is a records question, not a
    scheduling one, so it isn't offered here at all.
    """


class RouteGroupService:
    """Route group service for CRUD operations"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.timezone = ZoneInfo(settings.scheduler_timezone)

    def _today(self) -> date:
        """Today's date in the project's configured timezone."""
        return datetime.now(self.timezone).date()

    async def create_route_group(
        self, session: AsyncSession, route_group_data: RouteGroupCreate
    ) -> RouteGroupRead:
        """Create new route group"""
        route_group = RouteGroup.model_validate(route_group_data)
        session.add(route_group)
        await session.commit()
        return await self._read_back(session, route_group.route_group_id)

    async def update_route_group(
        self,
        session: AsyncSession,
        route_group_id: UUID,
        route_group_data: RouteGroupUpdate,
    ) -> RouteGroupRead | None:
        """Update existing route group"""
        statement = select(RouteGroup).where(
            RouteGroup.route_group_id == route_group_id
        )
        result = await session.execute(statement)
        route_group = result.scalars().first()

        if not route_group:
            self.logger.error(f"RouteGroup with id {route_group_id} not found")
            return None

        update_data = route_group_data.model_dump(exclude_unset=True)

        # Re-sending the same date is a no-op, so only an actual move is blocked.
        if (
            "drive_date" in update_data
            and update_data["drive_date"] != route_group.drive_date
            and await self._is_frozen(session, route_group_id)
        ):
            raise FrozenRouteGroupError(
                f"RouteGroup {route_group_id} has frozen routes; its drive date "
                f"({route_group.drive_date.isoformat()}) is part of the delivery "
                f"record and can no longer be changed."
            )

        for field, value in update_data.items():
            setattr(route_group, field, value)

        await session.commit()
        return await self._read_back(session, route_group_id)

    async def _is_frozen(self, session: AsyncSession, route_group_id: UUID) -> bool:
        """Whether any route in the group has been frozen (has a RouteSnapshot)."""
        result = await session.execute(
            select(RouteSnapshot.route_id)
            .join(Route, Route.route_id == RouteSnapshot.route_id)  # type: ignore[arg-type]
            .where(Route.route_group_id == route_group_id)
            .limit(1)
        )
        return result.first() is not None

    async def duplicate_route_group(
        self,
        session: AsyncSession,
        route_group_id: UUID,
        overrides: RouteGroupDuplicate | None = None,
    ) -> RouteGroupRead | None:
        """Duplicate a route group with fresh route/stop rows.

        `overrides` supplies the new group's name and drive_date; either falls
        back to the original ("Copy of {name}" / same date) when omitted.

        Route snapshots and note chains are intentionally not copied: they are
        historical records attached to the original route. New routes point
        back to their source through cloned_from_route_id.
        """
        statement = (
            select(RouteGroup)
            .options(selectinload(RouteGroup.routes).selectinload(Route.route_stops))  # type: ignore[arg-type]
            .where(RouteGroup.route_group_id == route_group_id)
        )
        result = await session.execute(statement)
        route_group = result.scalars().first()

        if not route_group:
            self.logger.error(f"RouteGroup with id {route_group_id} not found")
            return None

        default_name = f"{ROUTE_GROUP_COPY_PREFIX}{route_group.name}"[
            :ROUTE_GROUP_NAME_MAX_LENGTH
        ]
        duplicated_group = RouteGroup(
            name=(overrides.name if overrides and overrides.name else default_name),
            notes=route_group.notes,
            drive_date=(
                overrides.drive_date
                if overrides and overrides.drive_date
                else route_group.drive_date
            ),
        )
        session.add(duplicated_group)

        for route in sorted(route_group.routes, key=lambda item: item.name):
            duplicated_route = Route(
                name=route.name,
                notes=route.notes,
                length=route.length,
                encoded_polyline=route.encoded_polyline,
                polyline_updated_at=route.polyline_updated_at,
                ends_at_warehouse=route.ends_at_warehouse,
                start_time=route.start_time,
                route_group_id=duplicated_group.route_group_id,
                driver_id=route.driver_id,
                cloned_from_route_id=route.route_id,
            )
            duplicated_group.routes.append(duplicated_route)

            for stop in sorted(route.route_stops, key=lambda item: item.stop_number):
                duplicated_route.route_stops.append(
                    RouteStop(
                        route_id=duplicated_route.route_id,
                        location_id=stop.location_id,
                        stop_number=stop.stop_number,
                    )
                )

        await session.commit()
        return await self._read_back(session, duplicated_group.route_group_id)

    async def _read_back(
        self, session: AsyncSession, route_group_id: UUID
    ) -> RouteGroupRead:
        """Fetch the read model for a group that was just written.

        The group is known to exist (we just committed it), so a missing row is
        an internal error rather than a caller-facing 404.
        """
        read = await self.get_route_group_read(session, route_group_id)
        if read is None:
            raise RuntimeError(
                f"RouteGroup {route_group_id} not found immediately after write"
            )
        return read

    async def get_route_group_read(
        self, session: AsyncSession, route_group_id: UUID
    ) -> RouteGroupRead | None:
        """Get a single route group as a read model with aggregate stats."""
        children_per_box = await resolve_children_per_box(session)
        statement = (
            self._read_statement(children_per_box)
            .where(RouteGroup.route_group_id == route_group_id)
            .options(selectinload(RouteGroup.routes))  # type: ignore[arg-type]
        )
        result = await session.execute(statement)
        row = result.first()
        if row is None:
            return None
        return self._row_to_read(row, include_routes=False)

    def _read_statement(self, children_per_box: int) -> Any:
        """Base SELECT producing RouteGroupRead rows: the group entity plus
        aggregate stats (location/box/driver counts, delivery type, status)."""

        group_location_ids: Any = (
            select(distinct(RouteStop.location_id))  # type: ignore[arg-type]
            .select_from(Route)
            .join(RouteStop, Route.route_id == RouteStop.route_id)  # type: ignore[arg-type]
            .where(Route.route_group_id == RouteGroup.route_group_id)
            .correlate(RouteGroup)
        )

        num_locations_subq = (
            select(func.count(distinct(RouteStop.location_id)))  # type: ignore[arg-type]
            .select_from(Route)
            .join(RouteStop, Route.route_id == RouteStop.route_id)  # type: ignore[arg-type]
            .where(Route.route_group_id == RouteGroup.route_group_id)
            .correlate(RouteGroup)
            .scalar_subquery()
            .label("num_locations")
        )

        num_boxes_subq = (
            select(
                func.coalesce(
                    func.sum(box_count_expr(Location.num_children, children_per_box)),
                    0,
                )
            )
            .where(Location.location_id.in_(group_location_ids))  # type: ignore[attr-defined]
            .correlate(RouteGroup)
            .scalar_subquery()
            .label("num_boxes")
        )

        num_drivers_subq = (
            select(func.count(distinct(Route.driver_id)))  # type: ignore[arg-type]
            .where(Route.route_group_id == RouteGroup.route_group_id)
            .where(col(Route.driver_id).isnot(None))
            .correlate(RouteGroup)
            .scalar_subquery()
            .label("num_drivers_assigned")
        )

        # A group's delivery type is a property of the stops it serves, not of
        # the group: it is whatever its locations are. A group with no stops
        # yet has no delivery type to report, and reads NULL.
        # A group whose stops span more than one delivery type has no single
        # right answer here, and nothing yet enforces that they cannot. Ordering
        # makes the arbitrary pick at least a stable one, so the same group does
        # not report different types on consecutive loads.
        delivery_type_expr = (
            select(Location.delivery_type)
            .where(Location.location_id.in_(group_location_ids))  # type: ignore[attr-defined]
            .order_by(Location.delivery_type)
            .limit(1)
            .correlate(RouteGroup)
            .scalar_subquery()
            .label("delivery_type")
        )

        # Frozen is a property of the routes, not the group: one snapshotted
        # route makes the group's drive date part of the delivery record.
        frozen_expr = (
            select(1)
            .select_from(Route)
            .join(RouteSnapshot, RouteSnapshot.route_id == Route.route_id)  # type: ignore[arg-type]
            .where(Route.route_group_id == RouteGroup.route_group_id)
            .correlate(RouteGroup)
            .exists()
            .label("frozen")
        )

        today = self._today()

        status_expr = case(
            (RouteGroup.drive_date >= today, RouteStatusEnum.UPCOMING.value),  # type: ignore[arg-type]
            else_=RouteStatusEnum.COMPLETED.value,
        ).label("status")

        return select(  # type: ignore[call-overload]
            RouteGroup,
            num_locations_subq,
            num_boxes_subq,
            num_drivers_subq,
            delivery_type_expr,
            status_expr,
            frozen_expr,
        )

    @staticmethod
    def _row_to_read(row: Any, include_routes: bool) -> RouteGroupRead:
        """Convert a _read_statement result row into a RouteGroupRead."""
        rg: RouteGroup = row.RouteGroup

        routes: list[RouteReadSummary] = []
        if include_routes:
            for route in rg.routes:
                routes.append(
                    RouteReadSummary(
                        route_id=route.route_id,
                        name=route.name,
                        notes=route.notes,
                        length=route.length,
                    )
                )

        return RouteGroupRead(
            route_group_id=rg.route_group_id,
            name=rg.name,
            notes=rg.notes,
            drive_date=rg.drive_date,
            created_at=rg.created_at,
            updated_at=rg.updated_at,
            num_routes=rg.num_routes,
            num_locations=row.num_locations,
            num_boxes=row.num_boxes,
            num_drivers_assigned=row.num_drivers_assigned,
            delivery_type=row.delivery_type,
            status=row.status,
            frozen=row.frozen,
            routes=routes,
        )

    async def get_route_groups(
        self,
        session: AsyncSession,
        start_date: date | None = None,
        end_date: date | None = None,
        weekday: list[DriveDaysOfWeekEnum] | None = None,
        delivery_type: list[str] | None = None,
        route_status: list[RouteStatusEnum] | None = None,
        driver_assignment_status: list[DriverAssignmentStatusEnum] | None = None,
        include_routes: bool = False,
        search: str | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResponse[RouteGroupRead]:
        """Get route groups with optional date filtering and aggregate stats.

        ``search`` filters (case-insensitive substring) on the group name.

        Paginated like the routes and locations lists: filters and search are
        applied first, so a page is drawn from the matches rather than being
        filtered after slicing.
        """

        children_per_box = await resolve_children_per_box(session)
        statement = self._read_statement(children_per_box)

        if search and search.strip():
            statement = statement.where(
                col(RouteGroup.name).ilike(f"%{search.strip()}%")
            )

        if start_date:
            statement = statement.where(RouteGroup.drive_date >= start_date)
        if end_date:
            statement = statement.where(RouteGroup.drive_date <= end_date)

        # Weekday filter
        if weekday:
            dow_map = {
                DriveDaysOfWeekEnum.MON: 1,
                DriveDaysOfWeekEnum.TUE: 2,
                DriveDaysOfWeekEnum.WED: 3,
                DriveDaysOfWeekEnum.THU: 4,
                DriveDaysOfWeekEnum.FRI: 5,
            }
            dow_values = [dow_map[w] for w in weekday]
            statement = statement.where(
                func.extract("dow", RouteGroup.drive_date).in_(dow_values)  # type: ignore[arg-type]
            )

        # Delivery type filter: a group matches if any of its stops' locations
        # has one of the requested delivery types. (Built as select(...).exists()
        # because Exists has no .join().)
        if delivery_type:
            statement = statement.where(
                select(1)
                .select_from(Route)
                .join(RouteStop, RouteStop.route_id == Route.route_id)  # type: ignore[arg-type]
                .join(Location, Location.location_id == RouteStop.location_id)  # type: ignore[arg-type]
                .where(Route.route_group_id == RouteGroup.route_group_id)
                .where(col(Location.delivery_type).in_(delivery_type))
                .exists()
            )

        if route_status:
            today = self._today()
            thirty_days_ago = today - timedelta(days=30)

            status_conditions: list[Any] = []
            if RouteStatusEnum.UPCOMING in route_status:
                status_conditions.append(RouteGroup.drive_date >= today)

            if RouteStatusEnum.COMPLETED in route_status:
                status_conditions.append(
                    and_(
                        RouteGroup.drive_date < today,  # type: ignore[arg-type]
                        RouteGroup.drive_date >= thirty_days_ago,  # type: ignore[arg-type]
                    )
                )

            if RouteStatusEnum.ARCHIVED in route_status:
                status_conditions.append(RouteGroup.drive_date < thirty_days_ago)
            if status_conditions:
                statement = statement.where(or_(*status_conditions))

        # Driver assignment status filter. "Assigned" means the group is fully
        # staffed: it has routes and every one has a driver. "Unassigned" is the
        # exact complement — at least one route still has no driver, or the
        # group has no routes yet (so a partially-staffed group is Unassigned).
        if driver_assignment_status:
            route_exists = (
                exists()
                .select_from(Route)
                .where(Route.route_group_id == RouteGroup.route_group_id)  # type: ignore[arg-type]
            )
            unassigned_route_exists = (
                exists()
                .select_from(Route)
                .where(Route.route_group_id == RouteGroup.route_group_id)  # type: ignore[arg-type]
                .where(col(Route.driver_id).is_(None))
            )
            fully_assigned = and_(route_exists, ~unassigned_route_exists)

            assignment_conditions: list[Any] = []
            if DriverAssignmentStatusEnum.ASSIGNED in driver_assignment_status:
                assignment_conditions.append(fully_assigned)
            if DriverAssignmentStatusEnum.UNASSIGNED in driver_assignment_status:
                assignment_conditions.append(~fully_assigned)
            if assignment_conditions:
                statement = statement.where(or_(*assignment_conditions))

        statement = statement.options(selectinload(RouteGroup.routes))  # type: ignore[arg-type]
        # Groups routinely share a drive date, and paginate_query runs the count
        # and the page as separate statements — so ordering by the date alone
        # lets the database break ties differently between them and a row can be
        # skipped or repeated across page boundaries. Name then id makes the
        # order total, so every page is cut from the same sequence.
        statement = statement.order_by(
            RouteGroup.drive_date, RouteGroup.name, RouteGroup.route_group_id
        )

        if pagination is None:
            pagination = PaginationParams()

        result, total = await paginate_query(session, statement, pagination)
        rows = result.all()

        return PaginatedResponse.create(
            items=[self._row_to_read(row, include_routes) for row in rows],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def delete_route_group(
        self, session: AsyncSession, route_group_id: UUID
    ) -> bool:
        """Delete a route group. Cascades to its routes (and their stops +
        snapshots via further cascades)."""
        statement = select(RouteGroup).where(
            RouteGroup.route_group_id == route_group_id
        )
        result = await session.execute(statement)
        route_group = result.scalars().first()

        if not route_group:
            self.logger.error(f"RouteGroup with id {route_group_id} not found")
            return False

        await session.delete(route_group)
        await session.commit()

        return True

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import Integer, and_, case, distinct, exists, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.config import settings
from app.models.enum import (
    DeliveryTypeEnum,
    DriveDaysOfWeekEnum,
    DriverAssignmentStatusEnum,
    RouteStatusEnum,
)
from app.models.location import Location
from app.models.route import Route
from app.models.route_group import (
    RouteGroup,
    RouteGroupCreate,
    RouteGroupRead,
    RouteGroupUpdate,
    RouteReadSummary,
)
from app.models.route_stop import RouteStop


class RouteGroupService:
    """Route group service for CRUD operations"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.timezone = ZoneInfo(settings.scheduler_timezone)

    async def create_route_group(
        self, session: AsyncSession, route_group_data: RouteGroupCreate
    ) -> RouteGroup:
        """Create new route group"""
        route_group = RouteGroup.model_validate(route_group_data)
        session.add(route_group)
        await session.commit()
        await session.refresh(route_group, ["routes"])
        return route_group

    async def update_route_group(
        self,
        session: AsyncSession,
        route_group_id: UUID,
        route_group_data: RouteGroupUpdate,
    ) -> RouteGroup | None:
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
        for field, value in update_data.items():
            setattr(route_group, field, value)

        await session.commit()
        await session.refresh(route_group, ["routes"])

        return route_group

    async def get_route_groups(
        self,
        session: AsyncSession,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        weekday: list[DriveDaysOfWeekEnum] | None = None,
        delivery_type: list[DeliveryTypeEnum] | None = None,
        route_status: list[RouteStatusEnum] | None = None,
        driver_assignment_status: list[DriverAssignmentStatusEnum] | None = None,
        include_routes: bool = False,
    ) -> list[RouteGroupRead]:
        """Get route groups with optional date filtering and aggregate stats."""

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
                    func.cast(
                        func.sum(
                            func.ceil(func.coalesce(Location.num_children, 0) / 2.0)
                        ),
                        Integer,
                    ),
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

        has_school_subq = (
            select(1)
            .select_from(Route)
            .join(RouteStop, Route.route_id == RouteStop.route_id)  # type: ignore[arg-type]
            .join(Location, RouteStop.location_id == Location.location_id)  # type: ignore[arg-type]
            .where(
                Route.route_group_id == RouteGroup.route_group_id,
                Location.delivery_type == DeliveryTypeEnum.SCHOOL.value,
            )
            .correlate(RouteGroup)
        )

        has_locations_subq = (
            select(1)
            .select_from(Route)
            .join(RouteStop, Route.route_id == RouteStop.route_id)  # type: ignore[arg-type]
            .where(Route.route_group_id == RouteGroup.route_group_id)
            .correlate(RouteGroup)
        )

        delivery_type_expr = case(
            (has_school_subq.exists(), DeliveryTypeEnum.SCHOOL.value),
            (has_locations_subq.exists(), DeliveryTypeEnum.FAMILY.value),
            else_=None,
        ).label("delivery_type")

        now = datetime.now(self.timezone).replace(tzinfo=None)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        thirty_days_ago = now - timedelta(days=30)

        status_expr = case(
            (RouteGroup.drive_date >= today_start, RouteStatusEnum.UPCOMING.value),  # type: ignore[arg-type]
            (RouteGroup.drive_date >= thirty_days_ago, RouteStatusEnum.COMPLETED.value),  # type: ignore[arg-type]
            else_=RouteStatusEnum.ARCHIVED.value,
        ).label("status")

        statement = select(  # type: ignore[call-overload]
            RouteGroup,
            num_locations_subq,
            num_boxes_subq,
            num_drivers_subq,
            delivery_type_expr,
            status_expr,
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
        # has one of the requested delivery types.
        if delivery_type:
            delivery_conditions: list[Any] = []
            for dt in delivery_type:
                delivery_conditions.append(
                    exists()
                    .select_from(Route)
                    .join(RouteStop, RouteStop.route_id == Route.route_id)
                    .join(Location, Location.location_id == RouteStop.location_id)
                    .where(Route.route_group_id == RouteGroup.route_group_id)
                    .where(Location.delivery_type == dt)
                )
            if delivery_conditions:
                statement = statement.where(or_(*delivery_conditions))

        if route_status:
            now = datetime.now(self.timezone).replace(tzinfo=None)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            thirty_days_ago = now - timedelta(days=30)

            status_conditions: list[Any] = []
            if RouteStatusEnum.UPCOMING in route_status:
                status_conditions.append(RouteGroup.drive_date >= today_start)

            if RouteStatusEnum.COMPLETED in route_status:
                status_conditions.append(
                    and_(
                        RouteGroup.drive_date <= now,  # type: ignore[arg-type]
                        RouteGroup.drive_date >= thirty_days_ago,  # type: ignore[arg-type]
                    )
                )

            if RouteStatusEnum.ARCHIVED in route_status:
                status_conditions.append(RouteGroup.drive_date < thirty_days_ago)
            if status_conditions:
                statement = statement.where(or_(*status_conditions))

        # Driver assignment status filter: "Assigned" means at least one route
        # in this group has a driver_id; "Unassigned" means none do.
        if driver_assignment_status:
            assigned_exists = (
                exists()
                .select_from(Route)
                .where(Route.route_group_id == RouteGroup.route_group_id)  # type: ignore[arg-type]
                .where(col(Route.driver_id).isnot(None))
            )

            assignment_conditions: list[Any] = []
            if DriverAssignmentStatusEnum.ASSIGNED in driver_assignment_status:
                assignment_conditions.append(assigned_exists)
            if DriverAssignmentStatusEnum.UNASSIGNED in driver_assignment_status:
                assignment_conditions.append(~assigned_exists)
            if assignment_conditions:
                statement = statement.where(or_(*assignment_conditions))

        statement = statement.order_by(RouteGroup.drive_date)

        result = await session.execute(statement)
        rows = result.all()

        items: list[RouteGroupRead] = []
        for row in rows:
            rg: RouteGroup = row.RouteGroup
            await session.refresh(rg, ["routes"])

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

            items.append(
                RouteGroupRead(
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
                    routes=routes,
                )
            )

        return items

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

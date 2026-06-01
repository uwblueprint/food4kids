import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import and_, exists, func, or_
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
from app.models.route_group import RouteGroup, RouteGroupCreate, RouteGroupUpdate
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
    ) -> list[RouteGroup]:
        """Get route groups with optional filtering.

        `delivery_type` used to be inferred from school_name presence; it's
        now an explicit per-Location column joined via Route.route_group_id.
        `driver_assignment_status` similarly reads Route.driver_id directly
        instead of going through the dropped DriverAssignment table.
        """
        statement = select(RouteGroup)

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

        # Delivery type filter — true per-Location lookup now (was previously
        # derived from school_name).
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
            # Get the current date and time in the local timezone
            now = datetime.now(self.timezone).replace(tzinfo=None)
            # Get start of current day (midnight) to properly determine which routes are upcoming
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            # Calculate the cutoff date for archiving (exactly 30 days ago from right now)
            thirty_days_ago = now - timedelta(days=30)

            status_conditions: list[Any] = []
            if RouteStatusEnum.UPCOMING in route_status:
                status_conditions.append(RouteGroup.drive_date > today_start)

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

        # Driver assignment status filter — driver_id now lives directly on
        # Route (DriverAssignment table dropped). "Assigned" means at least
        # one route in this group has a driver; "Unassigned" means none do.
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

        statement = statement.order_by(RouteGroup.drive_date)  # type: ignore[arg-type]

        result = await session.execute(statement)
        route_groups = result.scalars().all()

        # Eager-load routes for each group (avoids async lazy-load surprises
        # in route_group_routes.py and so callers can access num_routes).
        for route_group in route_groups:
            await session.refresh(route_group, ["routes"])

        return list(route_groups)

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

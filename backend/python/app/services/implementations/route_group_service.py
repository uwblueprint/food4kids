import logging
from datetime import datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import and_, exists, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.models.driver_assignment import DriverAssignment
from app.models.enum import (
    DeliveryTypeEnum,
    DriveDaysOfWeekEnum,
    DriverAssignmentStatusEnum,
    RouteStatusEnum,
)
from app.models.location import Location
from app.models.route_group import RouteGroup, RouteGroupCreate, RouteGroupUpdate
from app.models.route_group_membership import RouteGroupMembership
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
        await session.refresh(route_group, ["route_group_memberships"])
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
        await session.refresh(route_group, ["route_group_memberships"])

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
    ) -> list[RouteGroup]:
        """Get route groups with optional date filtering"""
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

        # Delivery type filter
        if delivery_type:
            # Subquery to traverse memberships -> stops -> locations to check for a school name
            has_school_query = (
                select(1)
                .select_from(RouteGroupMembership)
                .join(RouteStop, RouteGroupMembership.route_id == RouteStop.route_id)  # type: ignore[arg-type]
                .join(Location, RouteStop.location_id == Location.location_id)  # type: ignore[arg-type]
                .where(
                    RouteGroupMembership.route_group_id == RouteGroup.route_group_id,
                    Location.school_name.isnot(None),  # type: ignore[union-attr]
                    Location.school_name != "",
                )
            )

            # Subquery to check if the route group has any locations at all (make sure we dont default empty routes to summer)
            has_locations_query = (
                select(1)
                .select_from(RouteGroupMembership)
                .join(RouteStop, RouteGroupMembership.route_id == RouteStop.route_id)  # type: ignore[arg-type]
                .where(RouteGroupMembership.route_group_id == RouteGroup.route_group_id)
            )

            delivery_conditions = []
            if DeliveryTypeEnum.SCHOOL_YEAR in delivery_type:
                delivery_conditions.append(has_school_query.exists())
            if DeliveryTypeEnum.SUMMER in delivery_type:
                delivery_conditions.append(
                    and_(has_locations_query.exists(), ~has_school_query.exists())
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

            status_conditions = []
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

        # Driver assignment status filter
        if driver_assignment_status:
            # Create subquery that checks for existing assignment
            assignment_exists = exists().where(
                DriverAssignment.route_group_id == RouteGroup.route_group_id  # type: ignore[arg-type]
            )

            assignment_conditions = []
            if DriverAssignmentStatusEnum.ASSIGNED in driver_assignment_status:
                assignment_conditions.append(assignment_exists)
            if DriverAssignmentStatusEnum.UNASSIGNED in driver_assignment_status:
                assignment_conditions.append(~assignment_exists)
            if assignment_conditions:
                statement = statement.where(or_(*assignment_conditions))

        statement = statement.order_by(RouteGroup.drive_date)  # type: ignore[arg-type]

        result = await session.execute(statement)
        route_groups = result.scalars().all()

        # Load relationships for all route groups to avoid lazy loading issues
        for route_group in route_groups:
            await session.refresh(route_group, ["route_group_memberships"])
            if include_routes:
                for membership in route_group.route_group_memberships:
                    await session.refresh(membership, ["route"])

        return list(route_groups)

    async def delete_route_group(
        self, session: AsyncSession, route_group_id: UUID
    ) -> bool:
        """Delete a route group and all its route group memberships"""
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

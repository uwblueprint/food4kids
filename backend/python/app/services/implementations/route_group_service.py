import logging
from datetime import datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import and_, exists, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.models.driver_assignment import DriverAssignment
from app.models.enum import (
    AllowedWeekdayEnum,
    DeliveryTypeEnum,
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
        weekday: AllowedWeekdayEnum | None = None,
        delivery_type: DeliveryTypeEnum | None = None,
        route_status: RouteStatusEnum | None = None,
        driver_assignment_status: DriverAssignmentStatusEnum | None = None,
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
                AllowedWeekdayEnum.TUE: 2,
                AllowedWeekdayEnum.WED: 3,
                AllowedWeekdayEnum.THU: 4,
            }
            statement = statement.where(
                func.extract("dow", RouteGroup.drive_date) == dow_map[weekday]  # type: ignore[arg-type]
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

            if delivery_type == DeliveryTypeEnum.SCHOOL_YEAR:
                # If at least one location with a school name, it's a school year route
                statement = statement.where(has_school_query.exists())
            elif delivery_type == DeliveryTypeEnum.SUMMER:
                # If no locations have a school name, it's a summer route
                statement = statement.where(~has_school_query.exists())

        if route_status:
            # Get the current date and time in the local timezone
            now = datetime.now(self.timezone).replace(tzinfo=None)
            # Calculate the cutoff date for archiving (exactly 30 days ago from right now)
            thirty_days_ago = now - timedelta(days=30)

            if route_status == RouteStatusEnum.UPCOMING:
                # Includes routes strictly after right now
                statement = statement.where(RouteGroup.drive_date > now)

            elif route_status == RouteStatusEnum.COMPLETED:
                # From 30 days ago up to (and including) right now
                statement = statement.where(
                    and_(
                        RouteGroup.drive_date <= now,  # type: ignore[arg-type]
                        RouteGroup.drive_date >= thirty_days_ago,  # type: ignore[arg-type]
                    )
                )

            elif route_status == RouteStatusEnum.ARCHIVED:
                # Strictly older than 30 days ago
                statement = statement.where(RouteGroup.drive_date < thirty_days_ago)

        # Driver assignment status filter
        if driver_assignment_status:
            # Create subquery that checks for existing assignment
            assignment_exists = exists().where(
                DriverAssignment.route_group_id == RouteGroup.route_group_id  # type: ignore[arg-type]
            )

            if driver_assignment_status == DriverAssignmentStatusEnum.ASSIGNED:
                statement = statement.where(assignment_exists)
            elif driver_assignment_status == DriverAssignmentStatusEnum.UNASSIGNED:
                statement = statement.where(~assignment_exists)

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

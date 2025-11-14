import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.driver_assignment import DriverAssignment
from app.models.route_group import RouteGroup, RouteGroupCreate, RouteGroupUpdate
from app.models.route_group_membership import RouteGroupMembership


class RouteGroupService:
    """Route group service for CRUD operations"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def create_route_group(
        self, session: AsyncSession, route_group_data: RouteGroupCreate
    ) -> RouteGroup:
        """Create new route group"""
        route_group = RouteGroup.model_validate(route_group_data)
        session.add(route_group)
        await session.commit()
        await session.refresh(route_group)
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
        await session.refresh(route_group)

        return route_group

    async def get_upcoming_unassigned_routes(self, session: AsyncSession, from_date: datetime) -> list[RouteGroup]:
        """Get route groups with routes that have no driver assignments for upcoming dates"""
        # Convert timezone-aware datetime to naive datetime for comparison
        if from_date.tzinfo is not None:
            from_date = from_date.replace(tzinfo=None)

        statement = (
            select(RouteGroup)
            .where(RouteGroup.drive_date >= from_date)
            .join(RouteGroupMembership)
            .outerjoin(DriverAssignment, DriverAssignment.route_id == RouteGroupMembership.route_id)
            .where(DriverAssignment.driver_assignment_id.is_(None))
            .distinct()
        )
        result = await session.execute(statement)
        return result.scalars().all()

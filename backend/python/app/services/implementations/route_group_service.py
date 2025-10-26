import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.route_group import RouteGroup, RouteGroupCreate, RouteGroupUpdate


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

    async def get_route_groups(
        self,
        session: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_routes: bool = False,
    ) -> list[RouteGroup]:
        """Get route groups with optional date filtering"""
        statement = select(RouteGroup)
        
        if start_date:
            statement = statement.where(RouteGroup.drive_date >= start_date)
        if end_date:
            statement = statement.where(RouteGroup.drive_date <= end_date)
        
        statement = statement.order_by(RouteGroup.drive_date)
        
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

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.route import Route, RouteCreate, RouteUpdate


class RouteService:
    """Route service for CRUD operations"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def create_route(
        self, session: AsyncSession, route_data: RouteCreate
    ) -> Route:
        """Create new route"""
        try:
            route = Route(**route_data.model_dump())
            session.add(route)
            await session.commit()
            await session.refresh(route)
            return route
        except Exception as error:
            self.logger.error(f"Failed to create route: {error!s}")
            await session.rollback()
            raise error

    async def get_route(self, session: AsyncSession, route_id: UUID) -> Route | None:
        """Get route by ID"""
        statement = select(Route).where(Route.route_id == route_id)
        result = await session.execute(statement)
        route = result.scalars().first()

        if not route:
            self.logger.error(f"Route with id {route_id} not found")
            return None
        
        return route

    async def update_route(
        self,
        session: AsyncSession,
        route_id: UUID,
        route_data: RouteUpdate,
    ) -> Route | None:
        """Update existing route"""
        try:
            statement = select(Route).where(Route.route_id == route_id)
            result = await session.execute(statement)
            route = result.scalars().first()

            if not route:
                self.logger.error(f"Route with id {route_id} not found")
                return None

            update_data = route_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(route, field, value)

            await session.commit()
            await session.refresh(route)

            return route
        except Exception as error:
            self.logger.error(f"Failed to update route: {error!s}")
            await session.rollback()
            raise error

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
            self.logger.error(f"Failed to delete route: {error!s}")
            await session.rollback()
            raise error
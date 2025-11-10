import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.route import Route


class RouteService:
    """
    Service class for handling route-related operations.

    This class provides methods to manage Route entities, such as deleting routes by their ID.
    While currently only the delete operation is implemented, this class is intended to be extended
    with additional route-related operations in the future.
    """
    def __init__(self, logger: logging.Logger):
        self.logger = logger

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

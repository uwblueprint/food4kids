from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.route_group import RouteGroup, RouteGroupCreate, RouteGroupUpdate


class IRouteGroupService(ABC):
    """
    RouteGroupService interface with route group management methods
    """

    @abstractmethod
    async def create_route_group(
        self, session: AsyncSession, route_group_data: RouteGroupCreate
    ) -> RouteGroup:
        """
        Create new route group

        :param session: database session
        :type session: AsyncSession
        :param route_group_data: Route group data to create
        :type route_group_data: RouteGroupCreate
        :return: Created route group
        :rtype: RouteGroup
        :raises Exception: if creation fails
        """
        pass

    @abstractmethod
    async def update_route_group(
        self,
        session: AsyncSession,
        route_group_id: UUID,
        route_group_data: RouteGroupUpdate,
    ) -> RouteGroup | None:
        """
        Update existing route group

        :param session: database session
        :type session: AsyncSession
        :param route_group_id: ID of the route group to update
        :type route_group_id: UUID
        :param route_group_data: Updated route group data
        :type route_group_data: RouteGroupUpdate
        :return: Updated route group or None if not found
        :rtype: RouteGroup | None
        :raises Exception: if update fails
        """
        pass

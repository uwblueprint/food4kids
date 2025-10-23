from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location_group import LocationGroup, LocationGroupUpdate


class ILocationGroupService(ABC):
    """
    LocationGroupService interface with location group management methods
    """

    @abstractmethod
    async def update_location_group(
        self,
        session: AsyncSession,
        location_group_id: UUID,
        location_group_data: LocationGroupUpdate,
    ) -> LocationGroup | None:
        """
        Update existing location group

        :param session: database session
        :type session: AsyncSession
        :param location_group_id: ID of the location group to update
        :type location_group_id: UUID
        :param location_group_data: Updated location group data
        :type location_group_data: LocationGroupUpdate
        :return: Updated location group or None if not found
        :rtype: LocationGroup | None
        :raises Exception: if update fails
        """
        pass

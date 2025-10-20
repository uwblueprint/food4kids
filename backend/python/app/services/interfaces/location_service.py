from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location, LocationCreate, LocationUpdate


class ILocationService(ABC):
    """
    LocationService interface with location management methods
    """

    @abstractmethod
    async def get_location_by_id(
        self, session: AsyncSession, location_id: UUID
    ) -> Location | None:
        """
        Get location associated with location_id

        :param session: database session
        :type session: AsyncSession
        :param location_id: location's id
        :type location_id: UUID
        :return: a Location with location's information
        :rtype: Location
        :raises Exception: if location retrieval fails
        """
        pass

    @abstractmethod
    async def get_locations(self, session: AsyncSession) -> list[Location]:
        """
        Get all locations

        :param session: database session
        :type session: AsyncSession
        :return: list of Location with locations' information
        :rtype: list[Location]
        :raises Exception: if locations retrieval fails
        """
        pass

    @abstractmethod
    async def create_location(
        self, session: AsyncSession, location: LocationCreate
    ) -> Location:
        """
        Create a new location

        :param session: database session
        :type session: AsyncSession
        :param location: LocationCreate object with location's information
        :type location: LocationCreate
        :return: the created Location
        :rtype: Location
        :raises Exception: if location creation fails
        """
        pass

    @abstractmethod
    async def delete_all_locations(self, session: AsyncSession) -> None:
        """
        Delete all locations

        :param session: database session
        :type session: AsyncSession
        :raises Exception: if deletion fails
        """
        pass

    @abstractmethod
    async def delete_location_by_id(
        self, session: AsyncSession, location_id: UUID
    ) -> bool:
        """
        Delete location associated with location_id

        :param session: database session
        :type session: AsyncSession
        :param location_id: location_id of location to be deleted
        :type location_id: UUID
        :return: True if deletion was successful, False otherwise
        :rtype: bool
        :raises Exception: if deletion fails
        """
        pass

    @abstractmethod
    async def update_location_by_id(
        self, session: AsyncSession, location_id: UUID, location: LocationUpdate
    ) -> Location:
        """
        Update location associated with location_id

        :param session: database session
        :type session: AsyncSession
        :param location_id: location_id of location to be updated
        :type location_id: UUID
        :param updated_location_data: LocationUpdate object with location's information to be updated
        :type location: LocationUpdate
        :return: the updated Location
        :rtype: Location
        :raises Exception: if update fails
        """
        pass
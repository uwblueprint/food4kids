from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.simple_entity import (
    SimpleEntity,
    SimpleEntityCreate,
    SimpleEntityUpdate,
)


class ISimpleEntityService(ABC):
    """
    A class to handle CRUD functionality for simple entities
    """

    @abstractmethod
    async def get_simple_entities(self, session: AsyncSession) -> list[SimpleEntity]:
        """Return a list of all simple entities

        :param session: database session
        :type session: AsyncSession
        :return: A list of SimpleEntity objects
        :rtype: list[SimpleEntity]
        """
        pass

    @abstractmethod
    async def get_simple_entity(
        self, session: AsyncSession, id: int
    ) -> SimpleEntity | None:
        """Return a SimpleEntity object based on id

        :param session: database session
        :type session: AsyncSession
        :param id: SimpleEntity id
        :type id: int
        :return: SimpleEntity object or None if not found
        :rtype: SimpleEntity | None
        :raises Exception: id retrieval fails
        """
        pass

    @abstractmethod
    async def create_simple_entity(
        self, session: AsyncSession, entity: SimpleEntityCreate
    ) -> SimpleEntity:
        """Create a new SimpleEntity object

        :param session: database session
        :type session: AsyncSession
        :param entity: SimpleEntity creation data
        :type entity: SimpleEntityCreate
        :return: Created SimpleEntity object
        :rtype: SimpleEntity
        :raises Exception: if simple entity fields are invalid
        """
        pass

    @abstractmethod
    async def update_simple_entity(
        self, session: AsyncSession, id: int, entity: SimpleEntityUpdate
    ) -> SimpleEntity | None:
        """Update existing simple entity

        :param session: database session
        :type session: AsyncSession
        :param id: SimpleEntity id
        :type id: int
        :param entity: SimpleEntity update data
        :type entity: SimpleEntityUpdate
        :return: Updated SimpleEntity object or None if not found
        :rtype: SimpleEntity | None
        """
        pass

    @abstractmethod
    async def delete_simple_entity(self, session: AsyncSession, id: int) -> bool:
        """Delete existing simple entity

        :param session: database session
        :type session: AsyncSession
        :param id: SimpleEntity id
        :type id: int
        :return: True if deleted successfully, False otherwise
        :rtype: bool
        """
        pass

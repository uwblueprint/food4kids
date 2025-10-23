from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entity import Entity, EntityCreate, EntityUpdate


class IEntityService(ABC):
    """
    A class to handle CRUD functionality for entities
    """

    @abstractmethod
    async def get_entities(self, session: AsyncSession) -> list[Entity]:
        """Return a list of all entities

        :param session: database session
        :type session: AsyncSession
        :return: A list of Entity objects
        :rtype: list[Entity]
        """
        pass

    @abstractmethod
    async def get_entity(self, session: AsyncSession, id: int) -> Entity | None:
        """Return an Entity object based on id

        :param session: database session
        :type session: AsyncSession
        :param id: Entity id
        :type id: int
        :return: Entity object or None if not found
        :rtype: Entity | None
        :raises Exception: id retrieval fails
        """
        pass

    @abstractmethod
    async def create_entity(
        self, session: AsyncSession, entity: EntityCreate
    ) -> Entity:
        """Create a new Entity object

        :param session: database session
        :type session: AsyncSession
        :param entity: Entity creation data
        :type entity: EntityCreate
        :return: Created Entity object
        :rtype: Entity
        :raises Exception: if entity fields are invalid
        """
        pass

    @abstractmethod
    async def update_entity(
        self, session: AsyncSession, id: int, entity: EntityUpdate
    ) -> Entity | None:
        """Update existing entity

        :param session: database session
        :type session: AsyncSession
        :param id: Entity id
        :type id: int
        :param entity: Entity update data
        :type entity: EntityUpdate
        :return: Updated Entity object or None if not found
        :rtype: Entity | None
        """
        pass

    @abstractmethod
    async def delete_entity(self, session: AsyncSession, id: int) -> bool:
        """Delete existing entity

        :param session: database session
        :type session: AsyncSession
        :param id: Entity id
        :type id: int
        :return: True if deleted successfully, False otherwise
        :rtype: bool
        """
        pass

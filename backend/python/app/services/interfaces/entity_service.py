from abc import ABC, abstractmethod
from typing import Optional

from app.models.entity import Entity, EntityCreate, EntityUpdate


class IEntityService(ABC):
    """
    A class to handle CRUD functionality for entities
    """

    @abstractmethod
    def get_entities(self) -> list[Entity]:
        """Return a list of all entities

        :return: A list of dictionaries from Entity objects
        :rtype: list of dictionaries
        """
        pass

    @abstractmethod
    def get_entity(self, id: int) -> Optional[Entity]:
        """Return a dictionary from the Entity object based on id

        :param id: Entity id
        :return: dictionary of Entity object
        :rtype: dictionary
        :raises Exception: id retrieval fails
        """
        pass

    @abstractmethod
    def create_entity(self, entity: EntityCreate) -> Entity:
        """Create a new Entity object

        :param entity: dictionary of entity fields
        :return: dictionary of Entity object
        :rtype: dictionary
        :raises Exception: if entity fields are invalid
        """
        pass

    @abstractmethod
    def update_entity(self, id: int, entity: EntityUpdate) -> Optional[Entity]:
        """Update existing entity

        :param entity: dictionary of entity fields
        :param id: Entity id
        :return: dictionary of Entity object
        :rtype: dictionary
        """
        pass

    @abstractmethod
    def delete_entity(self, id: int) -> Optional[int]:
        """Delete existing entity

        :param id: Entity id
        :return: id of the Entity deleted
        :rtype: integer
        """
        pass

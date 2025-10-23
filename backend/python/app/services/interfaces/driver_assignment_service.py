from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver_assignment import (
    DriverAssignment,
    DriverAssignmentCreate,
    DriverAssignmentUpdate,
)


class IDriverAssignmentService(ABC):
    """
    A class to handle CRUD functionality for simple entities
    """

    @abstractmethod
    async def get_driver_assignments(
        self, session: AsyncSession
    ) -> list[DriverAssignment]:
        """Return a list of all driver assignments

        :param session: a database session
        :type session: AsyncSession
        :return: A list of dictionaries from DriverAssignment objects
        :rtype: list of dictionaries
        """
        pass

    @abstractmethod
    async def create_driver_assignment(
        self, session: AsyncSession, driver_assignment_data: DriverAssignmentCreate
    ) -> DriverAssignment:
        """Create a new DriverAssignment object

        :param session: a database session
        :type session: AsyncSession
        :param driver_assignment_data: dictionary of DriverAssignment fields
        :return: dictionary of DriverAssignment object
        :rtype: dictionary
        :raises Exception: if driver assignment fields are invalid
        """
        pass

    @abstractmethod
    async def update_driver_assignment(
        self,
        session: AsyncSession,
        driver_assignment_id: UUID,
        driver_assignment_data: DriverAssignmentUpdate,
    ) -> DriverAssignment | None:
        """Update existing driver assignment

        :param session: a database session
        :type session: AsyncSession
        :param driver_assignment_id: driver assignment id
        :param driver_assignment_data: dictionary of driver assignment fields
        :return: dictionary of DriverAssignment object
        :rtype: dictionary
        """
        pass

    @abstractmethod
    async def delete_driver_assignment(
        self, session: AsyncSession, driver_assignment_id: UUID
    ) -> bool:
        """Delete existing driver assignment

        :param session: a database session
        :type session: AsyncSession
        :param driver_assignment_id: DriverAssignment id
        :return: bool indicating whether deletion was successful
        :rtype: boolean
        """
        pass

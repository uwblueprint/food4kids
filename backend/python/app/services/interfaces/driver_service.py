from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver, DriverCreate, DriverUpdate


class IDriverService(ABC):
    """
    DriverService interface with driver management methods
    """

    @abstractmethod
    async def get_driver_by_id(
        self, session: AsyncSession, driver_id: UUID
    ) -> Driver | None:
        """
        Get driver associated with driver_id

        :param session: database session
        :type session: AsyncSession
        :param driver_id: driver's id
        :type driver_id: UUID
        :return: a Driver with driver's information
        :rtype: Driver
        :raises Exception: if driver retrieval fails
        """
        pass

    @abstractmethod
    async def get_driver_by_email(
        self, session: AsyncSession, email: str
    ) -> Driver | None:
        """
        Get driver associated with email

        :param session: database session
        :type session: AsyncSession
        :param email: driver's email
        :type email: str
        :return: a Driver with driver's information
        :rtype: Driver
        :raises Exception: if driver retrieval fails
        """
        pass

    @abstractmethod
    async def get_driver_by_auth_id(
        self, session: AsyncSession, auth_id: str
    ) -> Driver | None:
        """
        Get driver associated with auth_id

        :param session: database session
        :type session: AsyncSession
        :param auth_id: driver's auth_id
        :type auth_id: str
        :return: a Driver with driver's information
        :rtype: Driver
        :raises Exception: if driver retrieval fails
        """
        pass

    @abstractmethod
    async def get_driver_id_by_auth_id(
        self, session: AsyncSession, auth_id: str
    ) -> UUID | None:
        """
        Get id of driver associated with auth_id

        :param session: database session
        :type session: AsyncSession
        :param auth_id: driver's auth_id
        :type auth_id: str
        :return: id of the driver
        :rtype: UUID
        :raises Exception: if driver_id retrieval fails
        """
        pass

    @abstractmethod
    async def get_auth_id_by_driver_id(
        self, session: AsyncSession, driver_id: UUID
    ) -> str | None:
        """
        Get auth_id of driver associated with driver_id

        :param session: database session
        :type session: AsyncSession
        :param driver_id: driver's id
        :type driver_id: UUID
        :return: auth_id of the driver
        :rtype: str
        :raises Exception: if auth_id retrieval fails
        """
        pass

    @abstractmethod
    async def get_drivers(self, session: AsyncSession) -> list[Driver]:
        """
        Get all drivers (possibly paginated in the future)

        :param session: database session
        :type session: AsyncSession
        :return: list of Drivers
        :rtype: List[Driver]
        :raises Exception: if driver retrieval fails
        """
        pass

    @abstractmethod
    async def create_driver(
        self,
        session: AsyncSession,
        driver: DriverCreate,
        auth_id: str | None = None,
        signup_method: str = "PASSWORD",
    ) -> Driver:
        """
        Create a driver, email verification configurable

        :param session: database session
        :type session: AsyncSession
        :param driver: the driver to be created
        :type driver: DriverCreate
        :param auth_id: driver's firebase auth id, defaults to None
        :type auth_id: string, optional
        :param signup_method: method of signup, defaults to "PASSWORD"
        :type signup_method: str, optional
        :return: the created driver
        :rtype: Driver
        :raises Exception: if driver creation fails
        """
        pass

    @abstractmethod
    async def update_driver_by_id(
        self, session: AsyncSession, driver_id: UUID, driver: DriverUpdate
    ) -> Driver | None:
        """
        Update a driver
        Note: the password cannot be updated using this method, use IAuthService.reset_password instead

        :param session: database session
        :type session: AsyncSession
        :param driver_id: driver's id
        :type driver_id: UUID
        :param driver: the driver to be updated
        :type driver: DriverUpdate
        :return: the updated driver
        :rtype: Driver
        :raises Exception: if driver update fails
        """
        pass

    @abstractmethod
    async def delete_driver_by_id(self, session: AsyncSession, driver_id: UUID) -> None:
        """
        Delete a driver by driver_id

        :param session: database session
        :type session: AsyncSession
        :param driver_id: driver_id of driver to be deleted
        :type driver_id: UUID
        :raises Exception: if driver deletion fails
        """
        pass

    @abstractmethod
    async def delete_driver_by_email(self, session: AsyncSession, email: str) -> None:
        """
        Delete a driver by email

        :param session: database session
        :type session: AsyncSession
        :param email: email of driver to be deleted
        :type email: str
        :raises Exception: if driver deletion fails
        """
        pass

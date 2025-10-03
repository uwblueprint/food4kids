from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserCreate, UserUpdate


class IUserService(ABC):
    """
    UserService interface with user management methods
    """

    @abstractmethod
    async def get_user_by_id(
        self, session: AsyncSession, user_id: int
    ) -> Optional[User]:
        """
        Get user associated with user_id

        :param session: database session
        :type session: AsyncSession
        :param user_id: user's id
        :type user_id: int
        :return: a UserDTO with user's information
        :rtype: UserDTO
        :raises Exception: if user retrieval fails
        """
        pass

    @abstractmethod
    async def get_user_by_email(
        self, session: AsyncSession, email: str
    ) -> Optional[User]:
        """
        Get user associated with email

        :param session: database session
        :type session: AsyncSession
        :param email: user's email
        :type email: str
        :return: a UserDTO with user's information
        :rtype: UserDTO
        :raises Exception: if user retrieval fails
        """
        pass

    @abstractmethod
    async def get_user_role_by_auth_id(
        self, session: AsyncSession, auth_id: str
    ) -> Optional[str]:
        """
        Get role of user associated with auth_id

        :param session: database session
        :type session: AsyncSession
        :param auth_id: user's auth_id
        :type auth_id: str
        :return: role of the user
        :rtype: str
        :raises Exception: if user role retrieval fails
        """
        pass

    @abstractmethod
    async def get_user_id_by_auth_id(
        self, session: AsyncSession, auth_id: str
    ) -> Optional[int]:
        """
        Get id of user associated with auth_id

        :param session: database session
        :type session: AsyncSession
        :param auth_id: user's auth_id
        :type auth_id: str
        :return: id of the user
        :rtype: str
        :raises Exception: if user_id retrieval fails
        """
        pass

    @abstractmethod
    async def get_auth_id_by_user_id(
        self, session: AsyncSession, user_id: int
    ) -> Optional[str]:
        """
        Get auth_id of user associated with user_id

        :param session: database session
        :type session: AsyncSession
        :param user_id: user's id
        :type user_id: int
        :return: auth_id of the user
        :rtype: str
        :raises Exception: if auth_id retrieval fails
        """
        pass

    @abstractmethod
    async def get_users(self, session: AsyncSession) -> list[User]:
        """
        Get all users (possibly paginated in the future)

        :param session: database session
        :type session: AsyncSession
        :return: list of UserDTOs
        :rtype: List[UserDTO]
        :raises Exception: if user retrieval fails
        """
        pass

    @abstractmethod
    async def create_user(
        self,
        session: AsyncSession,
        user: UserCreate,
        auth_id: Optional[str] = None,
        signup_method: str = "PASSWORD",
    ) -> User:
        """
        Create a user, email verification configurable

        :param session: database session
        :type session: AsyncSession
        :param user: the user to be created
        :type user: CreateUserDTO
        :param auth_id: user's firebase auth id, defaults to None
        :type auth_id: string, optional
        :param signup_method: method of signup, defaults to "PASSWORD"
        :type signup_method: str, optional
        :return: the created user
        :rtype: UserDTO
        :raises Exception: if user creation fails
        """
        pass

    @abstractmethod
    async def update_user_by_id(
        self, session: AsyncSession, user_id: int, user: UserUpdate
    ) -> Optional[User]:
        """
        Update a user
        Note: the password cannot be updated using this method, use IAuthService.reset_password instead

        :param session: database session
        :type session: AsyncSession
        :param user_id: user's id
        :type user_id: int
        :param user: the user to be updated
        :type user: UpdateUserDTO
        :return: the updated user
        :rtype: UserDTO
        :raises Exception: if user update fails
        """
        pass

    @abstractmethod
    async def delete_user_by_id(self, session: AsyncSession, user_id: int) -> None:
        """
        Delete a user by user_id

        :param session: database session
        :type session: AsyncSession
        :param user_id: user_id of user to be deleted
        :type user_id: int
        :raises Exception: if user deletion fails
        """
        pass

    @abstractmethod
    async def delete_user_by_email(self, session: AsyncSession, email: str) -> None:
        """
        Delete a user by email

        :param session: database session
        :type session: AsyncSession
        :param email: email of user to be deleted
        :type email: str
        :raises Exception: if user deletion fails
        """
        pass

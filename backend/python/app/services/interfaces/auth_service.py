from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class IAuthService(ABC):
    """
    AuthService interface with user authentication methods
    """

    @abstractmethod
    async def generate_token(
        self, session: AsyncSession, email: str, password: str
    ) -> tuple[Any, str]:
        """
        Generate a short-lived JWT access token and a long-lived refresh token
        when supplied user's email and password

        :param session: database session
        :type session: AsyncSession
        :param email: user's email
        :type email: str
        :param password: user's password
        :type password: str
        :return: AuthDTO object containing the access token, refresh token, and user info
        :rtype: tuple[AuthResponse, str]
        :raises Exception: if token generation fails
        """
        pass

    @abstractmethod
    async def revoke_tokens(self, session: AsyncSession, driver_id: Any) -> None:
        """
        Revoke all refresh tokens of a driver

        :param session: database session
        :type session: AsyncSession
        :param driver_id: driver_id of driver whose refresh tokens are to be revoked
        :type driver_id: UUID
        :raises Exception: if token revocation fails
        """
        pass

    @abstractmethod
    def renew_token(self, refresh_token: str) -> Any:
        """
        Generate new access and refresh token pair using the provided refresh token

        :param refresh_token: user's refresh token
        :type refresh_token: str
        :return: Token object containing new access and refresh tokens
        :rtype: TokenResponse
        :raises Exception: if token renewal fails
        """
        pass

    @abstractmethod
    def reset_password(self, email: str) -> None:
        """
        Generates a password reset link for the user with the given email
        and sends the reset link to that email address

        :param email: email of user requesting password reset
        :type email: str
        :raises Exception: if unable to generate link or send email
        """
        pass

    @abstractmethod
    def send_email_verification_link(self, email: str) -> None:
        """
        Generates an email verification link for the user with the given email
        and sends the reset link to that email address

        :param email: email of user requesting password reset
        :type email: str
        :raises Exception: if unable to generate link or send email
        """
        pass

    @abstractmethod
    async def is_authorized_by_role(
        self, session: AsyncSession, access_token: str, roles: set[str]
    ) -> bool:
        """
        Determine if the provided access token is valid and authorized for at least
        one of the specified roles

        :param session: database session
        :type session: AsyncSession
        :param access_token: user's access token
        :type access_token: str
        :param roles: roles to check for
        :type roles: set[str]
        :return: true if token valid and authorized, false otherwise
        :rtype: bool
        """
        pass

    @abstractmethod
    async def is_authorized_by_driver_id(
        self, session: AsyncSession, access_token: str, requested_driver_id: Any
    ) -> bool:
        """
        Determine if the provided access token is valid and issued to the requested driver

        :param session: database session
        :type session: AsyncSession
        :param access_token: driver's access token
        :type access_token: str
        :param requested_driver_id: driver_id of the requested driver
        :type requested_driver_id: UUID
        :return: true if token valid and authorized, false otherwise
        :rtype: bool
        """
        pass

    @abstractmethod
    def is_authorized_by_email(self, access_token: str, requested_email: str) -> bool:
        """
        Determine if the provided access token is valid and issued to the requested user
        with the specified email address

        :param access_token: user's access token
        :type access_token: str
        :param requested_email: email address of the requested user
        :type requested_email: str
        :return: true if token valid and authorized, false otherwise
        :rtype: bool
        """
        pass

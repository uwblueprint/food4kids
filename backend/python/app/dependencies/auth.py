# ruff: noqa
# mypy: ignore-errors

import logging
from collections.abc import Callable
from uuid import UUID

import firebase_admin.auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import get_session
from app.services.implementations.auth_service import AuthService
from app.services.implementations.driver_service import DriverService
from app.services.implementations.email_service import EmailService
from app.services.implementations.user_service import UserService

# Initialize services
logger = logging.getLogger(__name__)
driver_service = DriverService(logger)
user_service = UserService(logger)
email_service = EmailService(
    logger,
    {
        "refresh_token": settings.mailer_refresh_token,
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": settings.mailer_client_id,
        "client_secret": settings.mailer_client_secret,
    },
    settings.mailer_user,
    "Food4Kids",
)
auth_service = AuthService(logger, user_service, driver_service, email_service)

# Security scheme
security = HTTPBearer()


def get_access_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Extract access token from Authorization header"""
    return credentials.credentials


def require_authorization_by_role(roles: set[str]) -> Callable:
    """
    Create a dependency that checks if the user has one of the required roles

    :param roles: Set of authorized roles
    :return: FastAPI dependency function
    """

    async def check_role(
        access_token: str = Depends(get_access_token),
        session: AsyncSession = Depends(get_session),
    ) -> bool:
        authorized = await auth_service.is_authorized_by_role(
            session, access_token, roles
        )
        if not authorized:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to make this request.",
            )    
        return True

    return check_role


def require_authorization_by_user_id(user_id: str) -> Callable:
    """
    Create a dependency that checks if the user is authorized for a specific user_id

    :param user_id: The user ID to check authorization for
    :return: FastAPI dependency function
    """

    async def check_user_id(
        access_token: str = Depends(get_access_token),
        session: AsyncSession = Depends(get_session),
    ) -> bool:
        try:
            authorized = await auth_service.is_authorized_by_driver_id(
                session, access_token, UUID(user_id)
            )
            if not authorized:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="You are not authorized to make this request.",
                )
            return True
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to make this request.",
            ) from e

    return check_user_id


def require_authorization_by_email(email: str) -> Callable:
    """
    Create a dependency that checks if the user is authorized for a specific email

    :param email: The email to check authorization for
    :return: FastAPI dependency function
    """

    def check_email(access_token: str = Depends(get_access_token)) -> bool:
        try:
            authorized = auth_service.is_authorized_by_email(access_token, email)
            if not authorized:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="You are not authorized to make this request.",
                )
            return True
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to make this request.",
            ) from e

    return check_email


# Common authorization dependencies
require_driver = require_authorization_by_role({"Driver"})


def get_current_user_id(access_token: str = Depends(get_access_token)) -> str:
    """
    Get the current user ID from the access token

    :param access_token: JWT access token
    :return: User ID
    """
    try:
        decoded_token: dict[str, str] = firebase_admin.auth.verify_id_token(
            access_token, check_revoked=True
        )
        return str(decoded_token["uid"])
    except Exception as e:
        logger.error(f"Failed to decode access token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from e


def get_current_user_email(access_token: str = Depends(get_access_token)) -> str:
    """
    Get the current user email from the access token

    :param access_token: JWT access token
    :return: User email
    """
    try:
        decoded_token: dict[str, str] = firebase_admin.auth.verify_id_token(
            access_token, check_revoked=True
        )
        return str(decoded_token["email"])
    except Exception as e:
        logger.error(f"Failed to decode access token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from e


async def get_current_database_user_id(
    access_token: str = Depends(get_access_token),
    session: AsyncSession = Depends(get_session),
) -> UUID:
    """
    Get the current database user ID from the access token

    :param access_token: JWT access token
    :param session: Database session
    :return: Database user ID (UUID)
    """
    try:
        decoded_token: dict[str, str] = firebase_admin.auth.verify_id_token(
            access_token, check_revoked=True
        )
        firebase_uid = decoded_token["uid"]

        # Convert Firebase UID to database driver ID
        database_user_id = await user_service.get_user_id_by_auth_id(
            session, firebase_uid
        )
        if database_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        return database_user_id
    except Exception as e:
        logger.error(f"Failed to get database user ID from access token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from e

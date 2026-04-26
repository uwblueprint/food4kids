# ruff: noqa
# mypy: ignore-errors

import logging
from collections.abc import Callable
from uuid import UUID

import firebase_admin.auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import exists, select as sql_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import get_session
from app.models.driver_assignment import DriverAssignment
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
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to make this request.",
            )
        return True

    return check_role


async def require_self_driver_or_admin(
    driver_id: UUID,
    access_token: str = Depends(get_access_token),
    session: AsyncSession = Depends(get_session),
) -> bool:
    """
    Allow access if user is an admin, or if the authenticated user is the driver
    with the given driver_id. Used for GET /drivers/{driver_id}.
    """
    try:
        decoded_token = firebase_admin.auth.verify_id_token(
            access_token, check_revoked=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from e

    if decoded_token.get("role") == "admin":
        return True

    authorized = await auth_service.is_authorized_by_driver_id(
        session, access_token, driver_id
    )
    if not authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resource.",
        )
    return True


async def require_route_assigned_or_admin(
    route_id: UUID,
    access_token: str = Depends(get_access_token),
    session: AsyncSession = Depends(get_session),
) -> bool:
    """
    Allow access if user is an admin, or if the authenticated driver is assigned
    to the given route. Used for GET /routes/{route_id}.
    """
    try:
        decoded_token = firebase_admin.auth.verify_id_token(
            access_token, check_revoked=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from e

    if decoded_token.get("role") == "admin":
        return True

    # Get the driver_id for the authenticated user
    token_driver_id = await driver_service.get_driver_id_by_auth_id(
        session, decoded_token["uid"]
    )
    if token_driver_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resource.",
        )

    # Check if this driver has any assignment for this route
    result = await session.execute(
        sql_select(
            exists(
                sql_select(1)
                .select_from(DriverAssignment)
                .where(
                    DriverAssignment.driver_id == token_driver_id,
                    DriverAssignment.route_id == route_id,
                )
            )
        )
    )
    is_assigned = result.scalar()

    if not is_assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resource.",
        )
    return True


# Common authorization dependencies
require_admin = require_authorization_by_role({"admin"})
require_driver_or_admin = require_authorization_by_role({"driver", "admin"})


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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get database user ID from access token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from e

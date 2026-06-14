import logging
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

import firebase_admin.auth
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.models import get_session
from app.models.route import Route
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


def _verified_token(access_token: str) -> dict[str, Any]:
    """
    Verify the Firebase ID token once and require a verified email.

    ``email_verified`` is read from the token claim (it is part of the decoded
    ID token), so this performs a single Firebase call — no separate ``get_user``
    round-trip — and applies the same email-verification bar to every caller,
    admins included.

    :raises HTTPException: 401 if the token is invalid/expired, 403 if the
        caller's email is not verified.
    """
    try:
        decoded_token: dict[str, Any] = firebase_admin.auth.verify_id_token(
            access_token, check_revoked=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from e

    if not decoded_token.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address is not verified.",
        )
    return decoded_token


def _path_uuid(request: Request, param_name: str) -> UUID:
    """
    Read a UUID-valued path parameter by name, failing loudly if the route the
    auth dependency is attached to does not actually expose it.

    We read from ``request.path_params`` rather than declaring the parameter in
    the dependency signature on purpose. If an auth dependency declares e.g.
    ``driver_id: UUID`` and is attached to a route whose path has no
    ``{driver_id}``, FastAPI silently demotes it to a *required query parameter*
    — the ownership check would then compare against a client-supplied value
    decoupled from the resource in the URL, guarding nothing. Reading the path
    param explicitly turns that misconfiguration into an immediate error.
    """
    raw = request.path_params.get(param_name)
    if raw is None:
        raise RuntimeError(
            f"Auth dependency expected a '{{{param_name}}}' path parameter, but "
            f"the matched route '{request.url.path}' does not define one. "
            f"Refusing to authorize."
        )
    try:
        return UUID(raw)
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid {param_name}",
        ) from e


def require_authorization_by_role(roles: set[str]) -> Callable[..., Awaitable[bool]]:
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
    request: Request,
    access_token: str = Depends(get_access_token),
    session: AsyncSession = Depends(get_session),
) -> bool:
    """
    Allow access if the caller is an admin, or is the driver identified by the
    route's ``{driver_id}`` path parameter. Used for GET /drivers/{driver_id}.

    The token is verified once (with email_verified enforced for everyone,
    admins included). The driver_id is read from the path via ``_path_uuid``,
    which raises if the route does not define one rather than leaving the
    resource silently unguarded.
    """
    driver_id = _path_uuid(request, "driver_id")
    decoded_token = _verified_token(access_token)

    if decoded_token.get("role") == "admin":
        return True

    token_driver_id = await driver_service.get_driver_id_by_auth_id(
        session, decoded_token["uid"]
    )
    if token_driver_id != driver_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resource.",
        )
    return True


async def require_route_assigned_or_admin(
    request: Request,
    access_token: str = Depends(get_access_token),
    session: AsyncSession = Depends(get_session),
) -> bool:
    """
    Allow access if the caller is an admin, or is a driver assigned to the route
    identified by the ``{route_id}`` path parameter. Used for GET
    /routes/{route_id}.

    The token is verified once (with email_verified enforced for everyone,
    admins included). The route_id is read from the path via ``_path_uuid``,
    which raises if the route does not define one rather than leaving the
    resource silently unguarded.
    """
    route_id = _path_uuid(request, "route_id")
    decoded_token = _verified_token(access_token)

    if decoded_token.get("role") == "admin":
        return True

    token_driver_id = await driver_service.get_driver_id_by_auth_id(
        session, decoded_token["uid"]
    )
    if token_driver_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resource.",
        )

    # A driver "owns" a route iff route.driver_id matches their driver_id.
    is_assigned = await session.scalar(
        select(
            select(Route)
            .where(
                Route.route_id == route_id,
                Route.driver_id == token_driver_id,
            )
            .exists()
        )
    )
    if not is_assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resource.",
        )
    return True


# Common authorization dependencies
require_admin = require_authorization_by_role({"admin"})
require_driver = require_authorization_by_role({"driver"})
require_driver_or_admin = require_authorization_by_role({"driver", "admin"})


def get_current_user_email(access_token: str = Depends(get_access_token)) -> str:
    """
    Get the current user email from the access token

    :param access_token: JWT access token
    :return: User email
    """
    try:
        decoded_token: dict[str, Any] = firebase_admin.auth.verify_id_token(
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
        decoded_token: dict[str, Any] = firebase_admin.auth.verify_id_token(
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

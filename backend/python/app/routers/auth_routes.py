import logging
import traceback
from typing import Literal, cast
from uuid import UUID

import firebase_admin.auth
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies.auth import get_current_database_user_id, get_current_user_email
from app.dependencies.services import (
    get_auth_service,
    get_driver_service,
    get_user_service,
)
from app.models import get_session
from app.models.driver import DriverCreate, DriverRegister
from app.models.user import UserCreate
from app.schemas.auth import AuthResponse, LoginRequest, RefreshResponse
from app.services.implementations.auth_service import AuthService
from app.services.implementations.driver_service import DriverService
from app.services.implementations.user_service import UserService

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_cookie_options() -> dict[str, bool | Literal["none", "strict", "lax"]]:
    """Get cookie options based on environment"""
    samesite: Literal["none", "strict", "lax"] = (
        "none" if settings.preview_deploy else "strict"
    )
    return {
        "httponly": True,
        "samesite": samesite,
        "secure": settings.is_production,
    }


@router.post("/login", response_model=AuthResponse)
async def login(
    login_request: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """
    Returns access token in response body and sets refreshToken as an httpOnly cookie
    """
    logger.info(f"Login request: {login_request}")
    try:
        if not login_request.email or not login_request.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required",
            )
        auth_dto, refresh_token = await auth_service.generate_token(
            session, login_request.email, login_request.password
        )

        # Set refresh token as httpOnly cookie
        cookie_options = get_cookie_options()
        response.set_cookie(
            "refreshToken",
            value=refresh_token,
            httponly=bool(cookie_options["httponly"]),
            samesite=cast(
                "Literal['none', 'strict', 'lax']", cookie_options["samesite"]
            ),
            secure=bool(cookie_options["secure"]),
        )

        return auth_dto
    except ValueError as e:
        # Handle authentication failures (including user not found)
        # Always return 401 to prevent user enumeration attacks
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e
    except Exception as e:
        error_message = getattr(e, "message", None)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message if error_message else str(e),
        ) from e


@router.post("/register", response_model=AuthResponse)
async def register(
    register_request: DriverRegister,
    response: Response,
    session: AsyncSession = Depends(get_session),
    auth_service: AuthService = Depends(get_auth_service),
    driver_service: DriverService = Depends(get_driver_service),
    user_service: UserService = Depends(get_user_service),
) -> AuthResponse:
    """
    Returns access token and driver info in response body and sets refreshToken as an httpOnly cookie
    """
    user = None
    firebase_auth_id = None

    try:
        # Create user first
        user_data = register_request.model_dump(
            include=set(UserCreate.model_fields.keys())
        )
        user_create = UserCreate(**user_data)
        user = await user_service.create_user(session, user_create)
        firebase_auth_id = user.auth_id

        # Set custom claims on Firebase user
        firebase_admin.auth.set_custom_user_claims(user.auth_id, {"role": user.role})

        # Create driver after
        driver_data = register_request.model_dump(
            include=set(DriverCreate.model_fields.keys())
        )
        driver_data["user_id"] = user.user_id
        driver = DriverCreate(**driver_data)
        await driver_service.create_driver(session, driver)

        # Generate authentication tokens
        auth_dto, refresh_token = await auth_service.generate_token(
            session, register_request.email, register_request.password
        )

        # Send email verification link
        auth_service.send_email_verification_link(register_request.email)

        # Set refresh token as httpOnly cookie
        cookie_options = get_cookie_options()
        response.set_cookie(
            "refreshToken",
            value=refresh_token,
            httponly=bool(cookie_options["httponly"]),
            samesite=cast(
                "Literal['none', 'strict', 'lax']", cookie_options["samesite"]
            ),
            secure=bool(cookie_options["secure"]),
        )

        return auth_dto
    except Exception as e:
        # Compensating transaction: rollback all changes
        logger.error(f"Error registering driver: {e}")
        logger.error(traceback.format_exc())

        # Attempt to clean up database user (which also attempts Firebase cleanup)
        db_cleanup_failed = False
        if user:
            try:
                await user_service.delete_user_by_id(
                    session=session, user_id=user.user_id
                )
            except Exception as db_error:
                logger.error(f"Failed to rollback database user: {db_error}")
                db_cleanup_failed = True

        # If database cleanup failed and we have a Firebase auth_id, attempt direct Firebase cleanup
        # This ensures Firebase user is deleted even if database cleanup failed
        if db_cleanup_failed and firebase_auth_id:
            try:
                firebase_admin.auth.delete_user(firebase_auth_id)
                logger.info(
                    f"Successfully deleted Firebase user {firebase_auth_id} via direct cleanup"
                )
            except Exception as firebase_error:
                logger.error(
                    f"Failed to rollback Firebase user via direct cleanup: {firebase_error}"
                )

        error_message = getattr(e, "message", None)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message if error_message else str(e),
        ) from e


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    request: Request,
    response: Response,
    _session: AsyncSession = Depends(get_session),
    auth_service: AuthService = Depends(get_auth_service),
) -> RefreshResponse:
    """
    Returns access token in response body and sets refreshToken as an httpOnly cookie
    """
    try:
        refresh_token = request.cookies.get("refreshToken")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found",
            )

        token = auth_service.renew_token(refresh_token)

        # Set new refresh token as httpOnly cookie
        cookie_options = get_cookie_options()
        response.set_cookie(
            "refreshToken",
            value=token.refresh_token,
            httponly=bool(cookie_options["httponly"]),
            samesite=cast(
                "Literal['none', 'strict', 'lax']", cookie_options["samesite"]
            ),
            secure=bool(cookie_options["secure"]),
        )

        return RefreshResponse(access_token=token.access_token)
    except Exception as e:
        error_message = getattr(e, "message", None)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message if error_message else str(e),
        ) from e


@router.post("/logout/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_database_user_id: UUID = Depends(get_current_database_user_id),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """
    Revokes all of the specified driver's refresh tokens
    """
    # Check if the driver is authorized to logout this driver_id
    if user_id != current_database_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to logout this driver",
        )

    try:
        await auth_service.revoke_tokens(session, user_id)
    except Exception as e:
        error_message = getattr(e, "message", None)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message if error_message else str(e),
        ) from e


@router.post("/resetPassword/{email}", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    email: EmailStr,
    _session: AsyncSession = Depends(get_session),
    current_user_email: str = Depends(get_current_user_email),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """
    Triggers password reset for user with specified email (reset link will be emailed)
    """
    # Check if the user is authorized to reset this email's password
    if email != current_user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to reset this email's password",
        )

    try:
        auth_service.reset_password(email)
    except Exception as e:
        error_message = getattr(e, "message", None)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message if error_message else str(e),
        ) from e

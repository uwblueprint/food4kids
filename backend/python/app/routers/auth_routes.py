import logging
import traceback
from typing import Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies.auth import get_current_database_user_id, get_current_user_email
from app.models import get_session
from app.models.enum import RoleEnum
from app.models.user import UserCreate, UserRegister
from app.schemas.auth import AuthResponse, LoginRequest, RefreshResponse
from app.services.implementations.auth_service import AuthService
from app.services.implementations.email_service import EmailService
from app.services.implementations.user_service import UserService

# Initialize services
logger = logging.getLogger(__name__)
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
auth_service = AuthService(logger, user_service, email_service)

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
    register_request: UserRegister,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> AuthResponse:
    """
    Returns access token and user info in response body and sets refreshToken as an httpOnly cookie
    """
    try:
        # Create user with default role
        user_data = register_request.model_dump()
        user_data["role"] = RoleEnum.USER
        user = UserCreate(**user_data)

        await user_service.create_user(session, user)
        auth_dto, refresh_token = await auth_service.generate_token(
            session, register_request.email, register_request.password
        )

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
        logger.error(f"Error registering user: {e}")
        # Stack trace
        logger.error(traceback.format_exc())
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
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_database_user_id: int = Depends(get_current_database_user_id),
) -> None:
    """
    Revokes all of the specified user's refresh tokens
    """
    # Check if the user is authorized to logout this user_id
    if user_id != current_database_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to logout this user",
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

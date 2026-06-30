import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_database_user_id, get_current_user_email
from app.dependencies.services import (
    get_auth_service,
)
from app.models import get_session
from app.schemas.auth import AuthResponse, LoginRequest
from app.services.implementations.auth_service import AuthService
from app.utilities.cookies import set_refresh_token_cookie

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


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

        set_refresh_token_cookie(response, refresh_token)

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


_FIREBASE_401_CODES = {
    "TOKEN_EXPIRED",
    "INVALID_REFRESH_TOKEN",
    "INVALID_GRANT",
    "USER_DISABLED",
    "USER_NOT_FOUND",
}


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """
    Returns access token in response body and sets refreshToken as an httpOnly cookie
    """
    refresh_token = request.cookies.get("refreshToken")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    try:
        auth_data, new_refresh_token = await auth_service.renew_token(
            session, refresh_token
        )

        set_refresh_token_cookie(response, new_refresh_token)

        return auth_data
    except Exception as e:
        if str(e) in _FIREBASE_401_CODES:
            raise HTTPException(status_code=401, detail="Session expired") from e

        logger.error(f"Failed to refresh: {e}")
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

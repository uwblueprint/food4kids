import logging
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies.auth import get_current_database_user_id
from app.dependencies.services import (
    get_auth_service,
    get_password_reset_token_service,
    get_user_service,
    get_email_dispatcher,
)
from app.models import get_session
from app.models.password_reset_token import PASSWORD_RESET_TOKEN_EXPIRY_DAYS
from app.schemas.auth import AuthResponse, LoginRequest, ForgotPasswordRequest, UpdatePasswordRequest, ValidateResetTokenRequest
from app.services.implementations.auth_service import AuthService
from app.services.implementations.user_service import UserService
from app.services.implementations.email_dispatcher import EmailDispatcher
from app.services.implementations.password_reset_token_service import PasswordResetTokenService
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
    "DB_USER_MISSING",  # Not a Firebase code
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


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(
    forgot_password_request: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_session),
    token_service: PasswordResetTokenService = Depends(get_password_reset_token_service),
    user_service: UserService = Depends(get_user_service),
    email_service: EmailDispatcher = Depends(get_email_dispatcher)
) -> None:
    """
    Triggers password reset for user with specified email (reset link will be emailed)
    Returns 204 regardless to avoid enumeration attacks
    """
    email = forgot_password_request.email

    try:
        user = await user_service.get_user_by_email(session, email)

        if not user or not getattr(user, "auth_id", None):
            # Masking attack: Log it internally, but return a success status to the client
            logger.info(f"Password reset attempted for non-existent email: {email}")
            return
        
        raw_token = await token_service.create(session, user.user_id)

        reset_link = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/forgot-password/{raw_token}"

        await email_service.dispatch(
            email_type="reset-password",
            to=email,
            context={
                "Driver_Name_To_Replace": user.first_name,
                "Reset_Password_URL": reset_link,
                "Days_Till_Expiry": str(PASSWORD_RESET_TOKEN_EXPIRY_DAYS)
            }
        )
        
    except Exception as e:
        logger.exception(f"Internal error processing forgot-password for {email}: {e}")
        return
    
@router.post("/validate-reset-token", status_code=status.HTTP_204_NO_CONTENT)
async def validate_reset_token(
    request: ValidateResetTokenRequest,
    session: AsyncSession = Depends(get_session),
    token_service: PasswordResetTokenService = Depends(get_password_reset_token_service),
) -> None:
    """
    Validate that a password reset token exists, isn't used, and hasn't expired.
    """
    token_obj = await token_service.read(session, request.token)
    current_time = datetime.now(timezone.utc)

    if not token_obj or token_obj.is_used or current_time > token_obj.expires_at.replace(tzinfo=timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token."
        )

@router.post("/update-password", status_code=status.HTTP_204_NO_CONTENT)
async def update_password(
    update_password_request: UpdatePasswordRequest,
    session: AsyncSession = Depends(get_session),
    token_service: PasswordResetTokenService = Depends(get_password_reset_token_service),
    user_service: UserService = Depends(get_user_service),
) -> None:
    """
    Update an existing user's password if provided a valid password reset token
    """
    token_obj = await token_service.read(session, update_password_request.password_reset_token)
    current_time = datetime.now(timezone.utc)

    if not token_obj or token_obj.is_used or current_time > token_obj.expires_at.replace(tzinfo=timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token."
        )
    
    await token_service.mark_used(session, token_obj)
    
    try:
        user = token_obj.user
        await user_service.update_password(user.auth_id, update_password_request.new_password)
        
    except Exception as e:
        logger.exception(f"Internal error updating password for token {update_password_request.password_reset_token}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password. Please request a new reset link."
        )

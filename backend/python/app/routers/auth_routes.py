import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies.auth import get_current_database_user_id
from app.dependencies.services import (
    get_auth_service,
    get_email_dispatcher_depends,
    get_password_reset_token_service,
    get_user_invite_service,
    get_user_service,
)
from app.models import get_session
from app.models.password_reset_token import PASSWORD_RESET_TOKEN_EXPIRY_DAYS
from app.models.user_invite import UserInviteCreate
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    ResendOnboardingEmailRequest,
    UpdatePasswordRequest,
    ValidateResetTokenRequest,
)
from app.services.implementations.auth_service import AuthService, SessionExpiredError
from app.services.implementations.email_dispatcher import EmailDispatcher
from app.services.implementations.password_reset_token_service import (
    PasswordResetTokenService,
)
from app.services.implementations.user_invite_service import UserInviteService
from app.services.implementations.user_service import UserService
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
    # Never log login_request itself — its repr contains the plaintext password.
    logger.info(f"Login request for {login_request.email}")
    try:
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
    except SessionExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired"
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

    await auth_service.revoke_tokens(session, user_id)


@router.post("/resend-onboarding", status_code=status.HTTP_204_NO_CONTENT)
async def resend_onboarding_email(
    request: ResendOnboardingEmailRequest,
    session: AsyncSession = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
    user_invite_service: UserInviteService = Depends(get_user_invite_service),
    email_dispatcher: EmailDispatcher = Depends(get_email_dispatcher_depends),
) -> None:
    """
    Resends the onboarding/invite email to a pending user.
    Returns 204 regardless of input/status to prevent user enumeration attacks.
    """
    email = request.email

    try:
        async with session.begin_nested():
            # Retrieve and lock the user row to prevent race conditions during concurrent resends
            user = await user_service.get_user_by_email(session, email, for_update=True)
            if not user:
                logger.info(
                    f"Onboarding email resend attempted for non-existent email: {email}"
                )
                return

            if user.auth_id is not None:
                logger.info(
                    f"Onboarding email resend attempted for already registered email: {email}"
                )
                return

            await user_invite_service.delete_user_invite_by_user_id(
                session, user.user_id
            )

            user_invite_create = UserInviteCreate(user_id=user.user_id)
            user_invite = await user_invite_service.create_user_invite(
                session, user_invite_create
            )

        await session.commit()

        signup_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/create-password/{user_invite.user_invite_id}"
        user_name = f"{user.first_name} {user.last_name}".strip()

        await email_dispatcher.dispatch(
            email_type="account-creation",
            to=email,
            context={
                "Driver_Name_To_Replace": user_name if user_name else "Driver",
                "Sign_Up_URL": signup_url,
                "Hours_Till_Expiry": 48,
            },
        )

    except Exception as e:
        logger.exception(
            f"Internal error processing resend-onboarding for {email}: {e}"
        )
        return


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(
    forgot_password_request: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_session),
    token_service: PasswordResetTokenService = Depends(
        get_password_reset_token_service
    ),
    user_service: UserService = Depends(get_user_service),
    email_service: EmailDispatcher = Depends(get_email_dispatcher_depends),
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

        reset_link = (
            f"{settings.FRONTEND_BASE_URL.rstrip('/')}/forgot-password/{raw_token}"
        )

        await email_service.dispatch(
            email_type="reset-password",
            to=email,
            context={
                "Driver_Name_To_Replace": user.first_name,
                "Reset_Password_URL": reset_link,
                "Days_Till_Expiry": str(PASSWORD_RESET_TOKEN_EXPIRY_DAYS),
            },
        )

    except Exception as e:
        # The one broad catch left in a router, and it is not converting the
        # failure to a 500 — it is refusing to let the caller see one. A 500 for
        # a real address next to a 204 for an unknown one is the enumeration
        # oracle this endpoint exists to close. The traceback still gets logged.
        logger.exception(f"Internal error processing forgot-password for {email}: {e}")
        return


@router.post("/validate-reset-token", status_code=status.HTTP_204_NO_CONTENT)
async def validate_reset_token(
    request: ValidateResetTokenRequest,
    session: AsyncSession = Depends(get_session),
    token_service: PasswordResetTokenService = Depends(
        get_password_reset_token_service
    ),
) -> None:
    """
    Validate that a password reset token exists, isn't used, and hasn't expired.
    """
    token_obj = await token_service.read(session, request.password_reset_token)
    current_time = datetime.now(timezone.utc)

    if (
        not token_obj
        or token_obj.is_used
        or current_time > token_obj.expires_at.replace(tzinfo=timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )


@router.post("/update-password", status_code=status.HTTP_204_NO_CONTENT)
async def update_password(
    update_password_request: UpdatePasswordRequest,
    session: AsyncSession = Depends(get_session),
    token_service: PasswordResetTokenService = Depends(
        get_password_reset_token_service
    ),
    user_service: UserService = Depends(get_user_service),
) -> None:
    """
    Update an existing user's password if provided a valid password reset token
    """
    token_obj = await token_service.read(
        session, update_password_request.password_reset_token
    )
    current_time = datetime.now(timezone.utc)

    if (
        not token_obj
        or token_obj.is_used
        or current_time > token_obj.expires_at.replace(tzinfo=timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    user = token_obj.user

    if user.auth_id is None:
        raise RuntimeError(f"User {user.user_id} has a token but missing auth_id.")

    await user_service.update_password(
        user.auth_id, update_password_request.new_password
    )

    try:
        await token_service.mark_as_used(session, token_obj)
    except Exception:
        # The password did change, so answering 204 is the honest result even
        # though the token is still live — failing here would tell the caller to
        # try again with a password that already works. Logged loudly because a
        # reset token that outlives its use is a real hole, just not one the
        # caller can do anything about.
        logger.critical(
            "PASSWORD UPDATED BUT TOKEN %s NOT BURNED",
            update_password_request.password_reset_token,
        )
        return

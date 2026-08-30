import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies.services import (
    get_auth_service,
    get_email_dispatcher_depends,
    get_password_reset_token_service,
    get_user_invite_service,
    get_user_service,
)
from app.models import get_session
from app.models.password_reset_token import PASSWORD_RESET_TOKEN_EXPIRY_DAYS
from app.models.user import UserFinalize
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
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
from app.utilities.cookies import clear_auth_cookies, set_refresh_token_cookie

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
            session,
            login_request.email,
            login_request.password,
            login_request.remember_me,
        )

        set_refresh_token_cookie(response, refresh_token, login_request.remember_me)

        return auth_dto
    except ValueError as e:
        # Handle authentication failures (including user not found)
        # Always return 401 to prevent user enumeration attacks
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e


@router.post(
    "/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    registration_data: UserFinalize,
    response: Response,
    session: AsyncSession = Depends(get_session),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
    user_invite_service: UserInviteService = Depends(get_user_invite_service),
) -> AuthResponse:
    """
    Finish an invited account: create the Firebase user, stamp its role claim,
    fill in ``users.auth_id``, burn the invite, and log the caller in.

    Deliberately role-agnostic. ``UserInvite`` doesn't distinguish a driver from
    an admin and ``link_firebase_to_user`` reads the role off the user row, so
    one endpoint serves both — a driver invited by an admin and an admin created
    by ``python -m app.create_admin`` follow the identical link and page.

    Unauthenticated by necessity: the caller has no account yet. The invite id
    in the body *is* the credential — a single-use, 48-hour, unguessable UUID
    bound to one pre-created user row. It grants exactly the role that row
    already carries, so possession of a link can never escalate anyone.
    """
    async with session.begin_nested():
        # Validate invite token and lock the row to prevent race conditions
        user_invite = await user_invite_service.get_user_invite_by_id(
            session, registration_data.user_invite_id, for_update=True
        )

        if (
            not user_invite
            or user_invite.is_used
            or user_invite.expires_at < datetime.now(timezone.utc)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired registration link.",
            )

        # Create Firebase account for user
        user = user_invite.user
        await user_service.link_firebase_to_user(
            session, user, registration_data.password
        )

        user_invite.is_used = True

    await session.commit()

    # Generate authentication tokens
    auth_dto, refresh_token = await auth_service.generate_token(
        session, user.email, registration_data.password, remember_me=False
    )

    # Set refresh token as httpOnly cookie
    set_refresh_token_cookie(response, refresh_token, remember_me=False)

    return auth_dto


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

    remember_me = request.cookies.get("rememberMe") == "true"

    try:
        auth_data, new_refresh_token = await auth_service.renew_token(
            session, refresh_token, remember_me
        )

        set_refresh_token_cookie(response, new_refresh_token, remember_me)

        return auth_data
    except SessionExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired"
        ) from e


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """
    Revokes refresh tokens and clears cookies
    """
    try:
        refresh_token = request.cookies.get("refreshToken")
        if refresh_token:
            await auth_service.revoke_tokens_by_refresh_token(refresh_token)

    except Exception:
        logger.exception("Failed to revoke refresh tokens during logout")

    finally:
        # Always clear auth cookies
        clear_auth_cookies(response)


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

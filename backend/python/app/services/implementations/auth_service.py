from logging import Logger
from typing import TYPE_CHECKING
from uuid import UUID

import firebase_admin.auth
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.schemas.auth import AuthResponse
from app.utilities.firebase_rest_client import FirebaseRestClient

if TYPE_CHECKING:
    from firebase_admin.auth import UserRecord

    from app.services.implementations.driver_service import DriverService
    from app.services.implementations.email_service import EmailService
    from app.services.implementations.user_service import UserService


class AuthService:
    """
    AuthService implementation with user authentication methods
    """

    def __init__(
        self,
        logger: Logger,
        user_service: "UserService",
        driver_service: "DriverService",
        email_service: "EmailService | None" = None,
    ) -> None:
        """
        Create an instance of AuthService

        :param logger: application's logger instance
        :type logger: Logger
        :param user_service: a user_service instance
        :type user_service: IUserService
        :param email_service: an email_service instance
        :type email_service: Optional[IEmailService]
        """
        self.logger: Logger = logger
        self.user_service: UserService = user_service
        self.driver_service: DriverService = driver_service
        self.email_service: EmailService | None = email_service
        self.firebase_rest_client: FirebaseRestClient = FirebaseRestClient(logger)

    async def generate_token(
        self, session: AsyncSession, email: str, password: str
    ) -> tuple[AuthResponse, str]:
        try:
            # Always attempt Firebase authentication first
            token = self.firebase_rest_client.sign_in_with_password(email, password)

            # If Firebase auth succeeds, get user from database
            user = await self.user_service.get_user_by_email(session, email)

            if user is None:
                self.logger.warning(
                    f"Firebase user {email} exists but not found in database - potential data inconsistency"
                )
                raise ValueError("Invalid email or password")

            # Create AuthResponse with all required fields (refresh_token excluded - it goes in httpOnly cookie)
            auth_response = AuthResponse(
                access_token=token.access_token,
                id=user.user_id,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                role=user.role,
            )
            return auth_response, token.refresh_token
        except Exception as e:
            # Log the actual error for debugging but return generic message to client
            self.logger.error(f"Authentication failed for email {email}: {e!s}")
            # Always return the same generic error message to prevent enumeration
            raise ValueError("Invalid email or password") from e

    async def revoke_tokens(self, session: AsyncSession, user_id: UUID) -> None:
        try:
            auth_id = await self.user_service.get_auth_id_by_user_id(session, user_id)
            firebase_admin.auth.revoke_refresh_tokens(auth_id)
        except Exception as e:
            reason = getattr(e, "message", None)
            error_message = [
                f"Failed to revoke refresh tokens of user with id {user_id}",
                "Reason =",
                (reason if reason else str(e)),
            ]
            self.logger.error(" ".join(error_message))
            raise e

    async def renew_token(
        self, session: AsyncSession, refresh_token: str
    ) -> tuple[AuthResponse, str]:
        try:
            token_response = self.firebase_rest_client.refresh_token(refresh_token)
            new_access_token = token_response.access_token
            payload = jwt.decode(
                new_access_token,
                options={"verify_signature": False},
                algorithms=["RS256"],
            )
            auth_id = payload.get("sub", "")
            user = await self.user_service.get_user_by_auth_id(session, auth_id)

            if user is None:
                raise ValueError("DB_USER_MISSINGG: User associated with this token does not exist.")

            auth_response = AuthResponse(
                access_token=new_access_token,
                id=user.user_id,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                role=user.role,
            )
            return auth_response, token_response.refresh_token
        except Exception as e:
            self.logger.error(f"Failed to refresh token: {e}")
            raise e

    def reset_password(self, email: str) -> None:
        if not self.email_service:
            error_message = """
                Attempted to call reset_password but this instance of AuthService 
                does not have an EmailService instance
                """
            self.logger.error(error_message)
            raise Exception(error_message)

        try:
            reset_link = firebase_admin.auth.generate_password_reset_link(email)
            email_body = f"""
                Hello,
                <br><br>
                We have received a password reset request for your account. 
                Please click the following link to reset it. 
                <strong>This link is only valid for 1 hour.</strong>
                <br><br>
                <a href={reset_link}>Reset Password</a>
                """
            self.email_service.send_email(email, "Your Password Reset Link", email_body)
        except Exception as e:
            reason = getattr(e, "message", None)
            self.logger.error(
                f"Failed to send password reset link for {email}. Reason = {reason if reason else str(e)}"
            )
            raise e

    def send_create_password_email(self, email: str, user_invite_id: UUID) -> None:
        if not self.email_service:
            error_message = """
                Attempted to call send_create_password_email but this instance of AuthService 
                does not have an EmailService instance
                """
            self.logger.error(error_message)
            raise Exception(error_message)

        try:
            driver_signup_link = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/create-password/{user_invite_id}"
            email_body = f"""
                Hello,
                <br><br>
                Please click the following link to verify your email and activate your account.
                <strong>This link is only valid for 2 days.</strong>
                <br><br>
                <a href={driver_signup_link}>Verify email</a>
                """
            self.email_service.send_email(email, "Verify your email", email_body)
        except Exception as e:
            self.logger.error(
                f"Failed to generate email verification link for user with email {email}."
            )
            raise e

    async def is_authorized_by_role(
        self, _session: AsyncSession, access_token: str, roles: set[str]
    ) -> bool:
        try:
            decoded_id_token = firebase_admin.auth.verify_id_token(
                access_token, check_revoked=True, clock_skew_seconds=5
            )
            user_role = decoded_id_token.get("role")
            if not user_role:
                self.logger.warning(
                    f"User {decoded_id_token['uid']} has no role claim set"
                )
                return False
            # Allow if role is in the authorized set
            return user_role in roles
        except Exception as e:
            self.logger.error(f"Authorization failed: {type(e).__name__}: {e!s}")
            return False

    def is_authorized_by_email(self, access_token: str, requested_email: str) -> bool:
        try:
            decoded_id_token = firebase_admin.auth.verify_id_token(
                access_token, check_revoked=True
            )
            firebase_user: UserRecord = firebase_admin.auth.get_user(
                decoded_id_token["uid"]
            )
            return bool(
                firebase_user.email_verified
                and decoded_id_token["email"] == requested_email
            )
        except Exception as e:
            self.logger.error(
                f"Authorization by email failed: {type(e).__name__}: {e!s}"
            )
            return False

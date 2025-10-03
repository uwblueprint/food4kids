from logging import Logger

import firebase_admin.auth
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enum import RoleEnum
from app.models.user import UserCreate
from app.schemas.auth import AuthResponse, TokenResponse
from app.services.interfaces.auth_service import IAuthService
from app.services.interfaces.email_service import IEmailService
from app.services.interfaces.user_service import IUserService
from app.utilities.firebase_rest_client import FirebaseRestClient


class AuthService(IAuthService):
    """
    AuthService implementation with user authentication methods
    """

    def __init__(
        self,
        logger: Logger,
        user_service: IUserService,
        email_service: IEmailService | None = None,
    ) -> None:
        """
        Create an instance of AuthService

        :param logger: application's logger instance
        :type logger: Logger
        :param user_service: an user_service instance
        :type user_service: IUserService
        :param email_service: an email_service instance
        :type email_service: Optional[IEmailService]
        """
        self.logger: Logger = logger
        self.user_service: IUserService = user_service
        self.email_service: IEmailService | None = email_service
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
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,  # Now using email from User model
                role=user.role,
            )
            return auth_response, token.refresh_token
        except Exception as e:
            # Log the actual error for debugging but return generic message to client
            self.logger.error(f"Authentication failed for email {email}: {e!s}")
            # Always return the same generic error message to prevent enumeration
            raise ValueError("Invalid email or password") from e

    async def generate_token_for_oauth(
        self, session: AsyncSession, id_token: str
    ) -> AuthResponse:
        try:
            # Verify the ID token with Firebase
            decoded_token = firebase_admin.auth.verify_id_token(id_token)
            user_id = decoded_token["uid"]
            email = decoded_token["email"]

            # If user already has a login with this email, just return the token
            try:
                # Note: an error message will be logged from UserService if this lookup fails.
                # You may want to silence the logger for this special OAuth user lookup case
                user = await self.user_service.get_user_by_email(session, email)
                if user is None:
                    self.logger.warning(
                        f"Firebase user {email} exists but not found in database - potential data inconsistency"
                    )
                    raise ValueError("Invalid email or password")

                return AuthResponse(
                    access_token=id_token,
                    id=user.id,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    email=user.email,  # Now using email from User model
                    role=user.role,
                )
            except Exception:
                pass

            # Create new user for OAuth
            user = await self.user_service.create_user(
                session,
                UserCreate(
                    first_name=decoded_token.get("name", "").split()[0]
                    if decoded_token.get("name")
                    else "",
                    last_name=decoded_token.get("name", "").split()[-1]
                    if decoded_token.get("name")
                    else "",
                    email=email,
                    role=RoleEnum.USER,
                    password="",
                ),
                auth_id=user_id,
                signup_method="GOOGLE",
            )
            return AuthResponse(
                access_token=id_token,
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,  # Now using email from User model
                role=user.role,
            )
        except Exception as e:
            reason = getattr(e, "message", None)
            self.logger.error(
                f"Failed to generate token for user with OAuth id token. Reason = {reason if reason else str(e)}"
            )
            raise e

    async def revoke_tokens(self, session: AsyncSession, user_id: int) -> None:
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

    def renew_token(self, refresh_token: str) -> TokenResponse:
        try:
            token_response = self.firebase_rest_client.refresh_token(refresh_token)
            return token_response
        except Exception as e:
            self.logger.error("Failed to refresh token")
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

    def send_email_verification_link(self, email: str) -> None:
        if not self.email_service:
            error_message = """
                Attempted to call send_email_verification_link but this instance of AuthService 
                does not have an EmailService instance
                """
            self.logger.error(error_message)
            raise Exception(error_message)

        try:
            verification_link = firebase_admin.auth.generate_email_verification_link(
                email
            )
            email_body = f"""
                Hello,
                <br><br>
                Please click the following link to verify your email and activate your account.
                <strong>This link is only valid for 1 hour.</strong>
                <br><br>
                <a href={verification_link}>Verify email</a>
                """
            self.email_service.send_email(email, "Verify your email", email_body)
        except Exception as e:
            self.logger.error(
                f"Failed to generate email verification link for user with email {email}."
            )
            raise e

    async def is_authorized_by_role(
        self, session: AsyncSession, access_token: str, roles: set[str]
    ) -> bool:
        try:
            decoded_id_token = firebase_admin.auth.verify_id_token(
                access_token, check_revoked=True
            )
            user_role = await self.user_service.get_user_role_by_auth_id(
                session, decoded_id_token["uid"]
            )
            firebase_user = firebase_admin.auth.get_user(decoded_id_token["uid"])
            return bool(firebase_user.email_verified and user_role in roles)
        except Exception as e:
            self.logger.error(f"Authorization failed: {type(e).__name__}: {e!s}")
            return False

    async def is_authorized_by_user_id(
        self, session: AsyncSession, access_token: str, requested_user_id: int
    ) -> bool:
        try:
            decoded_id_token = firebase_admin.auth.verify_id_token(
                access_token, check_revoked=True
            )
            token_user_id = await self.user_service.get_user_id_by_auth_id(
                session, decoded_id_token["uid"]
            )
            firebase_user = firebase_admin.auth.get_user(decoded_id_token["uid"])
            return bool(
                firebase_user.email_verified and token_user_id == requested_user_id
            )
        except Exception as e:
            self.logger.error(
                f"Authorization by user ID failed: {type(e).__name__}: {e!s}"
            )
            return False

    def is_authorized_by_email(self, access_token: str, requested_email: str) -> bool:
        try:
            decoded_id_token = firebase_admin.auth.verify_id_token(
                access_token, check_revoked=True
            )
            firebase_user = firebase_admin.auth.get_user(decoded_id_token["uid"])
            return bool(
                firebase_user.email_verified
                and decoded_id_token["email"] == requested_email
            )
        except Exception as e:
            self.logger.error(
                f"Authorization by email failed: {type(e).__name__}: {e!s}"
            )
            return False

from logging import Logger
from typing import TYPE_CHECKING
from uuid import UUID

import firebase_admin.auth
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import AuthResponse
from app.utilities.firebase_rest_client import FirebaseRestClient, FirebaseRestError

if TYPE_CHECKING:
    from app.services.implementations.driver_service import DriverService
    from app.services.implementations.email_service import EmailService
    from app.services.implementations.user_service import UserService


class SessionExpiredError(Exception):
    """The refresh token can no longer produce a session; re-login is required.

    The one signal ``/auth/refresh`` maps to a 401. Raising this is how
    ``renew_token`` says "this is the client's problem, not ours" — everything
    else it lets out is an unexpected failure and becomes a 500.
    """


# Firebase error codes that mean the refresh token itself is finished. Any
# other code is a fault on our side or Firebase's, not an expired session.
REAUTH_REQUIRED_FIREBASE_CODES = frozenset(
    {
        "TOKEN_EXPIRED",
        "INVALID_REFRESH_TOKEN",
        "INVALID_GRANT",
        "USER_DISABLED",
        "USER_NOT_FOUND",
    }
)


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
        self, session: AsyncSession, email: str, password: str, remember_me: bool
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
                remember_me=remember_me,
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
        self, session: AsyncSession, refresh_token: str, remember_me: bool
    ) -> tuple[AuthResponse, str]:
        """Exchange a refresh token for a fresh session.

        :raises SessionExpiredError: if the token can no longer produce a
            session — Firebase rejected it, or it is valid but its user is no
            longer in our database. Both mean the client must log in again.
        """
        try:
            token_response = self.firebase_rest_client.refresh_token(refresh_token)
        except FirebaseRestError as e:
            if e.code in REAUTH_REQUIRED_FIREBASE_CODES:
                raise SessionExpiredError(
                    f"Firebase rejected the refresh token: {e.code}"
                ) from e
            raise

        new_access_token = token_response.access_token
        payload = jwt.decode(
            new_access_token,
            options={"verify_signature": False},
            algorithms=["RS256"],
        )
        auth_id = payload.get("sub", "")
        user = await self.user_service.get_user_by_auth_id(session, auth_id)

        if user is None:
            raise SessionExpiredError(
                f"No user in the database for Firebase auth_id {auth_id}"
            )

        auth_response = AuthResponse(
            access_token=new_access_token,
            id=user.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role=user.role,
            remember_me=remember_me,
        )
        return auth_response, token_response.refresh_token

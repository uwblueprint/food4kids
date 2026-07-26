"""Status-code contract for the ``/auth`` routes.

The handlers in ``app/routers/auth_routes.py`` used to wrap their bodies in a
broad ``except Exception`` that converted whatever it caught into a 500 —
including, since ``HTTPException`` subclasses ``Exception``, the deliberate 4xx
they had just raised. The blanket handlers are gone (unexpected errors now
reach ``UnhandledExceptionMiddleware``), but the contract is the same and is
still worth pinning: these tests cover all four handlers, plus the status codes
``/auth/login`` and ``/auth/refresh`` are meant to return for bad input and for
expired/unknown sessions.
"""

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from logging import getLogger
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi import HTTPException
from httpx import AsyncClient, Response

from app.dependencies.auth import get_current_database_user_id
from app.dependencies.services import (
    get_auth_service,
    get_password_reset_token_service,
    get_user_service,
)
from app.schemas.auth import TokenResponse
from app.services.implementations.auth_service import (
    REAUTH_REQUIRED_FIREBASE_CODES,
    AuthService,
    SessionExpiredError,
)
from app.utilities.firebase_rest_client import FirebaseRestError

USER_ID: UUID = uuid4()
EMAIL = "driver@example.com"


class StubAuthService:
    """Stands in for ``AuthService``; every method raises the configured error.

    The auth handlers only ever reach the service after their own guards have
    passed, so raising from here exercises the ``try`` body of each handler.
    """

    def __init__(self, error: Exception) -> None:
        self.error = error

    async def generate_token(self, *_args: Any, **_kwargs: Any) -> Any:
        raise self.error

    async def renew_token(self, *_args: Any, **_kwargs: Any) -> Any:
        raise self.error

    async def revoke_tokens(self, *_args: Any, **_kwargs: Any) -> None:
        raise self.error


class StubTokenService:
    """Returns a valid, unused, unexpired reset token so the handler's guards
    pass and execution reaches the ``try`` body."""

    async def read(self, *_args: Any, **_kwargs: Any) -> Any:
        user = MagicMock()
        user.user_id = USER_ID
        user.auth_id = "firebase-uid"
        token = MagicMock()
        token.is_used = False
        token.expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        token.user = user
        return token

    async def mark_as_used(self, *_args: Any, **_kwargs: Any) -> None:
        return None


class StubUserService:
    """``update_password`` is what the handler awaits inside its ``try``."""

    def __init__(self, error: Exception) -> None:
        self.error = error

    async def update_password(self, *_args: Any, **_kwargs: Any) -> None:
        raise self.error


Requester = Callable[[AsyncClient], Awaitable[Response]]

# One entry per auth handler: the extra dependency overrides it needs to reach
# its own body, and a callable that drives it. ``get_auth_service`` is
# overridden separately by each test so the stub can raise a per-test error.
AUTH_ENDPOINTS: list[Any] = [
    pytest.param(
        lambda _error: {},
        lambda client: client.post(
            "/auth/login", json={"email": EMAIL, "password": "correct horse"}
        ),
        id="login",
    ),
    pytest.param(
        lambda _error: {},
        lambda client: client.post(
            "/auth/refresh", headers={"Cookie": "refreshToken=stub-refresh-token"}
        ),
        id="refresh",
    ),
    pytest.param(
        lambda _error: {get_current_database_user_id: lambda: USER_ID},
        lambda client: client.post(f"/auth/logout/{USER_ID}"),
        id="logout",
    ),
    pytest.param(
        lambda error: {
            get_password_reset_token_service: lambda: StubTokenService(),
            get_user_service: lambda: StubUserService(error),
        },
        lambda client: client.post(
            "/auth/update-password",
            json={
                "password_reset_token": str(uuid4()),
                "new_password": "Securepassword123!",
            },
        ),
        id="update_password",
    ),
]


async def _client_raising(
    client_with_overrides: Any,
    error: Exception,
    overrides: Callable[[Exception], dict[Any, Any]] = lambda _error: {},
) -> AsyncClient:
    """Build a client whose service layer raises ``error``.

    ``overrides`` is a factory rather than a dict because handlers differ in
    which service they fail through: most reach ``AuthService``, while
    ``/auth/update-password`` fails through ``UserService``. It defaults to
    "nothing extra" so the callers that only need ``AuthService`` — most of
    them — do not have to spell an empty factory.
    """
    stub = StubAuthService(error)
    client: AsyncClient = await client_with_overrides(
        {get_auth_service: lambda: stub, **overrides(error)}
    )
    return client


class TestHandlerExceptionMapping:
    """Nothing between the handler and the client rewrites a deliberate 4xx."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("overrides", "request_fn"), AUTH_ENDPOINTS)
    async def test_http_exception_in_body_keeps_its_status(
        self,
        client_with_overrides: Any,
        overrides: Any,
        request_fn: Requester,
    ) -> None:
        """A 4xx raised inside the handler body reaches the client unchanged."""
        error = HTTPException(status_code=409, detail="deliberate conflict")
        client = await _client_raising(client_with_overrides, error, overrides)

        response = await request_fn(client)

        assert response.status_code == 409
        assert response.json()["detail"] == "deliberate conflict"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("overrides", "request_fn"), AUTH_ENDPOINTS)
    async def test_unexpected_error_in_body_is_still_a_500(
        self,
        client_with_overrides: Any,
        overrides: Any,
        request_fn: Requester,
    ) -> None:
        """Genuinely unexpected failures keep mapping to 500."""
        client = await _client_raising(
            client_with_overrides, RuntimeError("database on fire"), overrides
        )

        response = await request_fn(client)

        assert response.status_code == 500


class TestLoginValidation:
    """``LoginRequest`` validation is Pydantic's job, not the handler's."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("payload", "expected_status"),
        [
            # Rejected by Pydantic before the handler runs.
            pytest.param({"password": "pw"}, 422, id="email-missing"),
            pytest.param({"email": EMAIL}, 422, id="password-missing"),
            pytest.param({}, 422, id="both-missing"),
            pytest.param({"email": "", "password": "pw"}, 422, id="email-empty"),
            pytest.param(
                {"email": "not-an-email", "password": "pw"}, 422, id="email-malformed"
            ),
            pytest.param({"email": None, "password": "pw"}, 422, id="email-null"),
            pytest.param({"email": EMAIL, "password": None}, 422, id="password-null"),
            # Well-formed: reaches the service, which rejects the credentials.
            # An empty password is a failed login (401), not a malformed request.
            pytest.param({"email": EMAIL, "password": ""}, 401, id="password-empty"),
            pytest.param({"email": EMAIL, "password": "wrong"}, 401, id="password-bad"),
        ],
    )
    async def test_login_status_codes(
        self,
        client_with_overrides: Any,
        payload: dict[str, Any],
        expected_status: int,
    ) -> None:
        client = await _client_raising(
            client_with_overrides, ValueError("Invalid email or password")
        )

        response = await client.post("/auth/login", json=payload)

        assert response.status_code == expected_status

    @pytest.mark.asyncio
    async def test_failed_login_does_not_reveal_which_field_was_wrong(
        self, client_with_overrides: Any
    ) -> None:
        """Authentication failures return one generic 401 (no user enumeration)."""
        client = await _client_raising(
            client_with_overrides, ValueError("Invalid email or password")
        )

        response = await client.post(
            "/auth/login", json={"email": EMAIL, "password": "wrong"}
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"


class TestRefresh:
    @pytest.mark.asyncio
    async def test_missing_cookie_is_401(self, client_with_overrides: Any) -> None:
        client = await _client_raising(
            client_with_overrides, AssertionError("service must not be reached")
        )

        response = await client.post("/auth/refresh")

        assert response.status_code == 401
        assert response.json()["detail"] == "Refresh token not found"

    @pytest.mark.asyncio
    async def test_session_expired_is_401(self, client_with_overrides: Any) -> None:
        """``SessionExpiredError`` is the one signal that means "log in again"."""
        client = await _client_raising(
            client_with_overrides, SessionExpiredError("token is finished")
        )

        response = await client.post(
            "/auth/refresh", headers={"Cookie": "refreshToken=stub-refresh-token"}
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Session expired"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "error",
        [
            pytest.param(ValueError("SOMETHING_ELSE"), id="value-error"),
            # Every one of these used to reach the router, which decided by
            # comparing str(e) to a set it owned. Now only the service's own
            # SessionExpiredError means 401 — a raw Firebase error is a 500,
            # even one whose text looks exactly like a session-ended code.
            pytest.param(FirebaseRestError("TOKEN_EXPIRED"), id="raw-firebase-code"),
            pytest.param(RuntimeError("database on fire"), id="runtime-error"),
        ],
    )
    async def test_anything_else_is_500(
        self, client_with_overrides: Any, error: Exception
    ) -> None:
        client = await _client_raising(client_with_overrides, error)

        response = await client.post(
            "/auth/refresh", headers={"Cookie": "refreshToken=stub-refresh-token"}
        )

        assert response.status_code == 500


class TestRenewTokenSessionExpiry:
    """``renew_token`` is the single place that decides "log in again".

    Before, it signalled by *message*: it raised with a bare error code that
    the router string-matched against a set. That contract broke silently the
    moment the message carried a typo or any extra prose — which is exactly
    what #216 found. These tests pin the decision at the service, where it
    belongs, so the router needs to know only one exception type.
    """

    def _service(
        self, user: Any = None, refresh_error: Exception | None = None
    ) -> AuthService:
        user_service = MagicMock()
        user_service.get_user_by_auth_id = AsyncMock(return_value=user)
        service = AuthService(getLogger(__name__), user_service, MagicMock())
        firebase_client: Any = MagicMock()
        if refresh_error is not None:
            firebase_client.refresh_token.side_effect = refresh_error
        else:
            firebase_client.refresh_token.return_value = TokenResponse(
                # renew_token decodes without verifying, so any well-formed
                # token carrying a "sub" claim will do.
                access_token=jwt.encode({"sub": "firebase-uid"}, "k" * 32, "HS256"),
                refresh_token="new-refresh-token",
            )
        service.firebase_rest_client = firebase_client
        return service

    @pytest.mark.asyncio
    async def test_missing_db_user_is_a_session_expiry(self) -> None:
        """A token Firebase still honours, for a user we no longer have."""
        service = self._service(user=None)

        with pytest.raises(SessionExpiredError):
            await service.renew_token(MagicMock(), "stub-refresh-token")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("code", sorted(REAUTH_REQUIRED_FIREBASE_CODES))
    async def test_reauth_firebase_codes_become_session_expiry(self, code: str) -> None:
        """Each code Firebase uses for a dead token maps to the domain error."""
        service = self._service(refresh_error=FirebaseRestError(code))

        with pytest.raises(SessionExpiredError):
            await service.renew_token(MagicMock(), "stub-refresh-token")

    @pytest.mark.asyncio
    async def test_other_firebase_codes_are_not_swallowed(self) -> None:
        """An unexpected Firebase failure must stay unexpected — a 500, not a
        401 that tells the user to log in again for no reason."""
        service = self._service(refresh_error=FirebaseRestError("QUOTA_EXCEEDED"))

        with pytest.raises(FirebaseRestError) as excinfo:
            await service.renew_token(MagicMock(), "stub-refresh-token")

        assert excinfo.value.code == "QUOTA_EXCEEDED"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "service_kwargs",
        [
            pytest.param({"user": None}, id="missing-db-user"),
            pytest.param(
                {"refresh_error": FirebaseRestError("TOKEN_EXPIRED")},
                id="firebase-rejected-token",
            ),
        ],
    )
    async def test_session_expiry_surfaces_as_401_through_the_route(
        self, client_with_overrides: Any, service_kwargs: dict[str, Any]
    ) -> None:
        """End-to-end through the real service: no string contract in between."""
        service = self._service(**service_kwargs)
        client: AsyncClient = await client_with_overrides(
            {get_auth_service: lambda: service}
        )

        response = await client.post(
            "/auth/refresh", headers={"Cookie": "refreshToken=stub-refresh-token"}
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Session expired"

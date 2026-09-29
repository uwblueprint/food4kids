"""Auth rate limiting: the limiter, `client_ip`, and the live endpoints."""

from collections.abc import AsyncGenerator
from datetime import timedelta
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import create_app
from app.dependencies.rate_limit import (
    EMAIL_SEND_EMAIL_LIMIT,
    EMAIL_SEND_IP_LIMIT,
    LOGIN_EMAIL_LIMIT,
    LOGIN_IP_LIMIT,
    RESET_TOKEN_IP_LIMIT,
    RateLimiter,
    client_ip,
)
from app.dependencies.services import (
    get_email_dispatcher_depends,
    get_password_reset_token_service,
)
from app.models import get_session
from app.models.password_reset_token import PasswordResetToken
from app.models.user_invite import UserInvite
from app.routers.auth_routes import (
    RESEND_EMAIL_COOLDOWN_SECONDS,
    _within_resend_cooldown,
)
from app.utilities.datetime_utils import now_utc


class FakeClock:
    """A manually advanced monotonic clock."""

    def __init__(self) -> None:
        self.now = 1_000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def build_limiter(
    limit: int = 3, window_seconds: float = 60.0
) -> tuple[
    RateLimiter,
    FakeClock,
]:
    clock = FakeClock()
    limiter = RateLimiter(
        name="test", limit=limit, window_seconds=window_seconds, clock=clock
    )
    return limiter, clock


# ---------------------------------------------------------------------------
# RateLimiter
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("limit", [1, 2, 5, 20])
def test_allows_exactly_limit_requests_then_rejects(limit: int) -> None:
    limiter, _ = build_limiter(limit=limit)

    for i in range(limit):
        limiter.check("key")  # must not raise
        assert limiter._windows["key"].count == i + 1

    with pytest.raises(HTTPException) as exc:
        limiter.check("key")
    assert exc.value.status_code == 429


def test_rejection_carries_retry_after_within_the_window() -> None:
    limiter, clock = build_limiter(limit=1, window_seconds=60.0)
    limiter.check("key")

    clock.advance(10)
    with pytest.raises(HTTPException) as exc:
        limiter.check("key")

    assert exc.value.headers is not None
    retry_after = int(exc.value.headers["Retry-After"])
    # 50s of the window remain; never advertise 0 (which clients read as "now").
    assert 1 <= retry_after <= 60
    assert retry_after >= 50


def test_window_rollover_admits_requests_again() -> None:
    limiter, clock = build_limiter(limit=2, window_seconds=60.0)
    limiter.check("key")
    limiter.check("key")
    with pytest.raises(HTTPException):
        limiter.check("key")

    # Just shy of the boundary: still blocked.
    clock.advance(59.9)
    with pytest.raises(HTTPException):
        limiter.check("key")

    clock.advance(0.1)
    limiter.check("key")  # window rolled over
    assert limiter._windows["key"].count == 1


def test_hammering_does_not_extend_the_lockout() -> None:
    """A rejected request must not restart the window, or an attacker who keeps
    retrying would lock the real user out indefinitely."""
    limiter, clock = build_limiter(limit=1, window_seconds=60.0)
    limiter.check("key")

    for _ in range(50):
        clock.advance(1)
        with pytest.raises(HTTPException):
            limiter.check("key")

    clock.advance(10)  # 60s total since the window opened
    limiter.check("key")


def test_keys_are_counted_independently() -> None:
    limiter, _ = build_limiter(limit=1)
    limiter.check("a")
    limiter.check("b")

    with pytest.raises(HTTPException):
        limiter.check("a")
    limiter.check("c")  # unaffected by a's exhaustion


def test_expired_windows_are_pruned_but_live_ones_survive() -> None:
    limiter, clock = build_limiter(limit=1, window_seconds=60.0)
    limiter.check("live")
    for i in range(1023):
        limiter.check(f"old-{i}")
    assert len(limiter._windows) == 1024

    clock.advance(30)  # "live" is mid-window; nothing has expired yet
    limiter.check("trigger")  # crosses the prune threshold
    assert "live" in limiter._windows
    with pytest.raises(HTTPException):
        limiter.check("live")

    clock.advance(60)  # every window, "trigger" included, has now expired...
    limiter._prune_at = 1  # ...so the next new key prunes them all
    limiter.check("fresh")
    assert set(limiter._windows) == {"fresh"}


def test_rejection_is_logged_once_per_window(caplog: Any) -> None:
    """A flood of 429s must not become a flood of log lines (Cloud Run bills them)."""
    limiter, clock = build_limiter(limit=1, window_seconds=60.0)
    limiter.check("key")
    with caplog.at_level("WARNING", logger="app.dependencies.rate_limit"):
        for _ in range(20):
            with pytest.raises(HTTPException):
                limiter.check("key")
    assert len(caplog.records) == 1

    clock.advance(60)
    limiter.check("key")
    with (
        caplog.at_level("WARNING", logger="app.dependencies.rate_limit"),
        pytest.raises(HTTPException),
    ):
        limiter.check("key")
    assert len(caplog.records) == 2  # a new window logs again


@pytest.mark.parametrize(
    "kwargs,message",
    [
        ({"limit": 0, "window_seconds": 60}, "limit must be at least 1"),
        ({"limit": 1, "window_seconds": 0}, "window_seconds must be positive"),
    ],
)
def test_rejects_nonsensical_configuration(
    kwargs: dict[str, Any], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        RateLimiter(name="bad", **kwargs)


def test_reset_clears_counters() -> None:
    limiter, _ = build_limiter(limit=1)
    limiter.check("key")
    with pytest.raises(HTTPException):
        limiter.check("key")

    limiter.reset()
    limiter.check("key")


# ---------------------------------------------------------------------------
# client_ip
# ---------------------------------------------------------------------------


def make_request(
    forwarded_for: str | None = None, peer: str | None = "10.0.0.1"
) -> Any:
    """Minimal ASGI scope — enough for Starlette's Request accessors."""
    from starlette.requests import Request

    headers = []
    if forwarded_for is not None:
        headers.append((b"x-forwarded-for", forwarded_for.encode()))

    scope: dict[str, Any] = {
        "type": "http",
        "method": "POST",
        "path": "/api/auth/login",
        "headers": headers,
    }
    if peer is not None:
        scope["client"] = (peer, 12345)

    return Request(scope)


def test_client_ip_falls_back_to_the_peer_without_a_forwarded_header() -> None:
    assert client_ip(make_request()) == "10.0.0.1"


def test_client_ip_uses_a_single_forwarded_entry() -> None:
    assert client_ip(make_request(forwarded_for="203.0.113.5")) == "203.0.113.5"


def test_client_ip_ignores_a_spoofed_leftmost_entry() -> None:
    """The security-critical case. A caller can put anything at the front of
    X-Forwarded-For; proxies append rather than validate. Trusting the leftmost
    entry would let an attacker rotate that value and get a fresh bucket per
    request, defeating the per-IP limit entirely."""
    spoofed = make_request(forwarded_for="1.2.3.4, 203.0.113.5")
    assert client_ip(spoofed) == "203.0.113.5"


@pytest.mark.parametrize(
    "header,expected",
    [
        ("  203.0.113.5  ", "203.0.113.5"),
        ("1.2.3.4,203.0.113.5", "203.0.113.5"),
        ("1.2.3.4 , 203.0.113.5 ", "203.0.113.5"),
        ("1.2.3.4, , 203.0.113.5", "203.0.113.5"),
        ("2001:db8::1", "2001:db8::1"),
    ],
)
def test_client_ip_parses_header_whitespace_and_ipv6(
    header: str, expected: str
) -> None:
    assert client_ip(make_request(forwarded_for=header)) == expected


def test_client_ip_falls_back_to_the_peer_for_an_empty_header() -> None:
    assert client_ip(make_request(forwarded_for="   ,  ")) == "10.0.0.1"


def test_client_ip_buckets_together_when_nothing_identifies_the_caller() -> None:
    """No header and no peer must share one bucket rather than skip the limit."""
    assert client_ip(make_request(forwarded_for=None, peer=None)) == "unknown"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def dispatched_emails(
    test_session: AsyncSession,
) -> AsyncGenerator[tuple[AsyncClient, list[dict[str, Any]]], None]:
    """An app whose email dispatcher records instead of sending."""
    sent: list[dict[str, Any]] = []

    dispatcher = AsyncMock()

    async def record(**kwargs: Any) -> None:
        sent.append(kwargs)

    dispatcher.dispatch = AsyncMock(side_effect=record)

    app = create_app()

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield test_session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_email_dispatcher_depends] = lambda: dispatcher

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, sent


async def _make_driver_user(
    test_session: AsyncSession, *, label: str, auth_id: str | None
) -> Any:
    """A driver-role user; `get_user_by_email` refuses non-admins with no driver row."""
    from app.models.driver import Driver
    from app.models.user import User

    user = User(
        first_name=label.title(),
        last_name="Tester",
        email=f"{label}-{uuid4().hex[:8]}@example.com",
        auth_id=auth_id,
    )
    test_session.add(user)
    test_session.add(
        Driver(
            user_id=user.user_id,
            phone="+15195550100",
            address="1 Test St",
            license_plate="TEST123",
            car_make_model="Test Car",
        )
    )
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def registered_user(test_session: AsyncSession) -> Any:
    """Finished sign-up: has an auth_id, so reset emails go out."""
    return await _make_driver_user(
        test_session, label="reset", auth_id=f"auth-{uuid4().hex[:8]}"
    )


@pytest_asyncio.fixture
async def pending_user(test_session: AsyncSession) -> Any:
    """Invited but not signed up (no auth_id), so onboarding emails go out."""
    return await _make_driver_user(test_session, label="pending", auth_id=None)


def xff(ip: str) -> dict[str, str]:
    return {"X-Forwarded-For": ip}


async def post(client: AsyncClient, endpoint: str, email: str, ip: str) -> Any:
    return await client.post(
        f"/api/auth/{endpoint}",
        json={"email": email},
        headers=xff(ip),
    )


@pytest.mark.asyncio
async def test_forgot_password_rejects_past_the_per_email_limit(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
) -> None:
    client, _ = dispatched_emails
    email = "victim@example.com"

    # Spread across distinct IPs so the per-IP limit cannot be what fires.
    for i in range(EMAIL_SEND_EMAIL_LIMIT.limit):
        response = await post(client, "forgot-password", email, f"198.51.100.{i}")
        assert response.status_code == 204, response.text

    blocked = await post(client, "forgot-password", email, "198.51.100.200")
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0


@pytest.mark.asyncio
async def test_forgot_password_rejects_past_the_per_ip_limit(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
) -> None:
    """One host walking a list of addresses is stopped by the IP limit even
    though no single address is repeated."""
    client, _ = dispatched_emails

    # A rotating spoofed entry in front of the real peer must not help.
    for i in range(EMAIL_SEND_IP_LIMIT.limit):
        response = await post(
            client,
            "forgot-password",
            f"person-{i}@example.com",
            f"10.0.0.{i}, 203.0.113.9",
        )
        assert response.status_code == 204, response.text

    blocked = await post(
        client, "forgot-password", "one-more@example.com", "10.0.0.99, 203.0.113.9"
    )
    assert blocked.status_code == 429


@pytest.mark.asyncio
async def test_forgot_password_limit_does_not_reveal_whether_an_account_exists(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
    registered_user: Any,
) -> None:
    """A real address and a made-up one must be indistinguishable, both while
    under the limit and once it trips."""
    client, _ = dispatched_emails

    observed = {}
    for label, email, ip_prefix in (
        ("real", registered_user.email, "192.0.2"),
        ("fake", "definitely-not-a-user@example.com", "198.18.0"),
    ):
        codes = []
        for i in range(EMAIL_SEND_EMAIL_LIMIT.limit + 1):
            response = await post(client, "forgot-password", email, f"{ip_prefix}.{i}")
            codes.append(response.status_code)
        observed[label] = codes

    assert observed["real"] == observed["fake"]
    assert observed["real"][-1] == 429
    assert set(observed["real"][:-1]) == {204}


@pytest.mark.asyncio
async def test_forgot_password_cooldown_suppresses_a_second_email_silently(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
    registered_user: Any,
) -> None:
    client, sent = dispatched_emails

    first = await post(client, "forgot-password", registered_user.email, "192.0.2.10")
    assert first.status_code == 204
    assert len(sent) == 1

    second = await post(client, "forgot-password", registered_user.email, "192.0.2.11")
    # Still 204 — the cooldown can only be evaluated for an account that exists,
    # so surfacing it in the response would leak existence.
    assert second.status_code == 204
    assert len(sent) == 1, "cooldown should have suppressed the second email"


@pytest.mark.asyncio
async def test_forgot_password_sends_again_once_the_cooldown_elapses(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
    registered_user: Any,
    test_session: AsyncSession,
) -> None:
    client, sent = dispatched_emails

    await post(client, "forgot-password", registered_user.email, "192.0.2.20")
    assert len(sent) == 1

    # Age the stored token past the cooldown rather than sleeping for it.
    from sqlmodel import col, select

    result = await test_session.execute(
        select(PasswordResetToken).where(
            col(PasswordResetToken.user_id) == registered_user.user_id
        )
    )
    token_row = result.scalars().one()
    token_row.created_at = now_utc() - timedelta(
        seconds=RESEND_EMAIL_COOLDOWN_SECONDS + 5
    )
    test_session.add(token_row)
    await test_session.commit()

    again = await post(client, "forgot-password", registered_user.email, "192.0.2.21")
    assert again.status_code == 204
    assert len(sent) == 2


@pytest.mark.asyncio
async def test_cooldown_is_false_without_a_row(
    test_session: AsyncSession, registered_user: Any
) -> None:
    assert not await _within_resend_cooldown(
        test_session, PasswordResetToken, registered_user.user_id
    )
    assert not await _within_resend_cooldown(
        test_session, UserInvite, registered_user.user_id
    )


@pytest.mark.asyncio
async def test_cooldown_reads_the_stored_clock_correctly(
    test_session: AsyncSession, registered_user: Any
) -> None:
    """Guards the clock pairing: `created_at` is aware UTC (`now_utc`). A naive
    or local now() would read a just-written row as hours old and never
    suppress anything."""
    service = get_password_reset_token_service()
    await service.create(test_session, registered_user.user_id)

    assert await _within_resend_cooldown(
        test_session, PasswordResetToken, registered_user.user_id
    )


@pytest.mark.asyncio
async def test_cooldown_expires_exactly_at_the_boundary(
    test_session: AsyncSession, registered_user: Any
) -> None:
    invite = UserInvite(user_id=registered_user.user_id)
    test_session.add(invite)
    await test_session.commit()

    for age, expected in (
        (RESEND_EMAIL_COOLDOWN_SECONDS - 1, True),
        (RESEND_EMAIL_COOLDOWN_SECONDS + 1, False),
    ):
        invite.created_at = now_utc() - timedelta(seconds=age)
        test_session.add(invite)
        await test_session.commit()
        assert (
            await _within_resend_cooldown(
                test_session, UserInvite, registered_user.user_id
            )
            is expected
        ), f"age={age}s"


@pytest.mark.asyncio
async def test_resend_onboarding_shares_the_email_send_limit(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
) -> None:
    """One address gets one hourly email budget across both link endpoints,
    so alternating them does not double it."""
    client, _ = dispatched_emails
    email = "victim@example.com"

    for i in range(EMAIL_SEND_EMAIL_LIMIT.limit):
        path = "forgot-password" if i % 2 else "resend-onboarding"
        response = await client.post(
            f"/api/auth/{path}",
            json={"email": email},
            headers={"X-Forwarded-For": f"198.51.100.{i}"},
        )
        assert response.status_code == 204, (path, response.text)

    blocked = await post(client, "resend-onboarding", email, "198.51.100.200")
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0


@pytest.mark.asyncio
async def test_resend_onboarding_limit_does_not_reveal_whether_an_account_exists(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
    pending_user: Any,
) -> None:
    client, _ = dispatched_emails

    observed = {}
    for label, email, ip_prefix in (
        ("real", pending_user.email, "192.0.2"),
        ("fake", "nobody-here@example.com", "198.18.0"),
    ):
        codes = []
        for i in range(EMAIL_SEND_EMAIL_LIMIT.limit + 1):
            response = await post(
                client, "resend-onboarding", email, f"{ip_prefix}.{i}"
            )
            codes.append(response.status_code)
        observed[label] = codes

    assert observed["real"] == observed["fake"]
    assert observed["real"][-1] == 429


@pytest.mark.asyncio
async def test_resend_onboarding_cooldown_suppresses_a_second_email_silently(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
    pending_user: Any,
) -> None:
    client, sent = dispatched_emails

    first = await post(client, "resend-onboarding", pending_user.email, "192.0.2.30")
    assert first.status_code == 204
    assert len(sent) == 1

    second = await post(client, "resend-onboarding", pending_user.email, "192.0.2.31")
    assert second.status_code == 204
    assert len(sent) == 1, "cooldown should have suppressed the second email"


@pytest.mark.asyncio
async def test_resend_onboarding_sends_again_once_the_cooldown_elapses(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
    pending_user: Any,
    test_session: AsyncSession,
) -> None:
    client, sent = dispatched_emails

    await post(client, "resend-onboarding", pending_user.email, "192.0.2.40")
    assert len(sent) == 1

    from sqlmodel import col, select

    result = await test_session.execute(
        select(UserInvite).where(col(UserInvite.user_id) == pending_user.user_id)
    )
    invite = result.scalars().one()
    invite.created_at = now_utc() - timedelta(seconds=RESEND_EMAIL_COOLDOWN_SECONDS + 5)
    test_session.add(invite)
    await test_session.commit()

    again = await post(client, "resend-onboarding", pending_user.email, "192.0.2.41")
    assert again.status_code == 204
    assert len(sent) == 2


@pytest.mark.asyncio
async def test_login_rejects_past_the_per_email_limit(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
) -> None:
    client, _ = dispatched_emails
    email = "target@example.com"

    codes = []
    for i in range(LOGIN_EMAIL_LIMIT.limit + 1):
        response = await client.post(
            "/api/auth/login",
            json={"email": email, "password": f"guess-{i}"},
            headers=xff(f"198.51.100.{i}"),
        )
        codes.append(response.status_code)

    assert codes[-1] == 429
    assert 429 not in codes[:-1], codes


@pytest.mark.asyncio
async def test_login_rejects_past_the_per_ip_limit(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
) -> None:
    client, _ = dispatched_emails

    codes = []
    for i in range(LOGIN_IP_LIMIT.limit + 1):
        response = await client.post(
            "/api/auth/login",
            json={"email": f"user-{i}@example.com", "password": "whatever"},
            headers=xff("203.0.113.42"),
        )
        codes.append(response.status_code)

    assert codes[-1] == 429
    assert 429 not in codes[:-1], codes


@pytest.mark.asyncio
async def test_validate_reset_token_is_rate_limited(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
) -> None:
    client, _ = dispatched_emails

    codes = []
    for _ in range(RESET_TOKEN_IP_LIMIT.limit + 1):
        response = await client.post(
            "/api/auth/validate-reset-token",
            json={"password_reset_token": "not-a-real-token"},
            headers=xff("203.0.113.51"),
        )
        codes.append(response.status_code)

    assert codes[-1] == 429
    assert set(codes[:-1]) == {400}, codes


@pytest.mark.asyncio
async def test_update_password_is_rate_limited(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
) -> None:
    client, _ = dispatched_emails

    codes = []
    for _ in range(RESET_TOKEN_IP_LIMIT.limit + 1):
        response = await client.post(
            "/api/auth/update-password",
            json={
                "password_reset_token": "not-a-real-token",
                "new_password": "Str0ng!Passw0rd",
            },
            headers=xff("203.0.113.52"),
        )
        codes.append(response.status_code)

    assert codes[-1] == 429


@pytest.mark.asyncio
async def test_refresh_is_not_rate_limited(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
) -> None:
    """The SPA calls /auth/refresh on a timer; limiting it would log real users
    out mid-session."""
    client, _ = dispatched_emails

    for _ in range(LOGIN_IP_LIMIT.limit + 5):
        response = await client.post("/api/auth/refresh", headers=xff("203.0.113.60"))
        assert response.status_code != 429

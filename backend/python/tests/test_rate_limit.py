"""Tests for auth endpoint rate limiting.

Three layers:

1. ``RateLimiter`` in isolation — counting, window rollover, key independence,
   ``Retry-After``, and the bounded-memory guard. These drive an injected clock
   rather than sleeping.
2. ``client_ip`` — in particular that a client-supplied ``X-Forwarded-For``
   cannot be used to dodge a per-IP limit.
3. The real endpoints — that limits actually fire, that a 429 does not reveal
   whether an account exists, and that the resend cooldown suppresses a second
   email without changing the response.
"""

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
    FORGOT_PASSWORD_EMAIL_LIMIT,
    FORGOT_PASSWORD_IP_LIMIT,
    LOGIN_EMAIL_LIMIT,
    LOGIN_IP_LIMIT,
    RESET_TOKEN_IP_LIMIT,
    RateLimiter,
    client_ip,
    reset_all_rate_limiters,
)
from app.dependencies.services import (
    get_email_dispatcher_depends,
    get_password_reset_token_service,
)
from app.models import get_session
from app.models.base import now_est_naive
from app.models.password_reset_token import PasswordResetToken
from app.routers.auth_routes import RESET_EMAIL_COOLDOWN_SECONDS


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


def test_expired_windows_are_dropped_when_the_map_fills() -> None:
    from app.dependencies import rate_limit

    limiter, clock = build_limiter(limit=1, window_seconds=60.0)
    original_max = rate_limit._MAX_TRACKED_KEYS
    rate_limit._MAX_TRACKED_KEYS = 10
    try:
        for i in range(10):
            limiter.check(f"key-{i}")
        assert len(limiter._windows) == 10

        # All of those expire, so a new key reclaims their space rather than
        # tipping the limiter into its "stop tracking" mode.
        clock.advance(61)
        limiter.check("fresh")
        assert "fresh" in limiter._windows
        assert len(limiter._windows) == 1
    finally:
        rate_limit._MAX_TRACKED_KEYS = original_max


def test_live_windows_are_never_evicted_when_the_map_is_full() -> None:
    """Bounded memory must not come at the cost of dropping a live counter —
    that would hand an attacker a reset."""
    from app.dependencies import rate_limit

    limiter, _ = build_limiter(limit=1, window_seconds=60.0)
    original_max = rate_limit._MAX_TRACKED_KEYS
    rate_limit._MAX_TRACKED_KEYS = 3
    try:
        for i in range(3):
            limiter.check(f"key-{i}")

        limiter.check("overflow")  # not tracked, allowed through
        assert "overflow" not in limiter._windows

        # The existing keys are still enforced.
        for i in range(3):
            with pytest.raises(HTTPException):
                limiter.check(f"key-{i}")
    finally:
        rate_limit._MAX_TRACKED_KEYS = original_max


@pytest.mark.parametrize("limit", [0, -1])
def test_rejects_a_nonsensical_limit(limit: int) -> None:
    with pytest.raises(ValueError, match="limit must be at least 1"):
        RateLimiter(name="bad", limit=limit, window_seconds=60)


@pytest.mark.parametrize("window", [0, -5.0])
def test_rejects_a_nonsensical_window(window: float) -> None:
    with pytest.raises(ValueError, match="window_seconds must be positive"):
        RateLimiter(name="bad", limit=1, window_seconds=window)


def test_reset_clears_counters() -> None:
    limiter, _ = build_limiter(limit=1)
    limiter.check("key")
    with pytest.raises(HTTPException):
        limiter.check("key")

    limiter.reset()
    limiter.check("key")


def test_reset_all_covers_the_configured_endpoint_limiters() -> None:
    for limiter in (
        LOGIN_IP_LIMIT,
        LOGIN_EMAIL_LIMIT,
        FORGOT_PASSWORD_IP_LIMIT,
        FORGOT_PASSWORD_EMAIL_LIMIT,
        RESET_TOKEN_IP_LIMIT,
    ):
        limiter.check("someone")
        assert limiter._windows

    reset_all_rate_limiters()

    for limiter in (
        LOGIN_IP_LIMIT,
        LOGIN_EMAIL_LIMIT,
        FORGOT_PASSWORD_IP_LIMIT,
        FORGOT_PASSWORD_EMAIL_LIMIT,
        RESET_TOKEN_IP_LIMIT,
    ):
        assert not limiter._windows


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
        "path": "/auth/login",
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


def test_client_ip_is_stable_across_rotating_spoofed_entries() -> None:
    real = "203.0.113.5"
    seen = {
        client_ip(make_request(forwarded_for=f"9.9.9.{i}, {real}")) for i in range(50)
    }
    assert seen == {real}


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


@pytest_asyncio.fixture
async def registered_user(test_session: AsyncSession) -> Any:
    from app.models.user import User

    user = User(
        first_name="Reset",
        last_name="Tester",
        email=f"reset-{uuid4().hex[:8]}@example.com",
        auth_id=f"auth-{uuid4().hex[:8]}",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


def headers_for(ip: str) -> dict[str, str]:
    return {"X-Forwarded-For": ip}


@pytest.mark.asyncio
async def test_forgot_password_rejects_past_the_per_email_limit(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
) -> None:
    client, _ = dispatched_emails
    email = "victim@example.com"

    # Spread across distinct IPs so the per-IP limit cannot be what fires.
    for i in range(FORGOT_PASSWORD_EMAIL_LIMIT.limit):
        response = await client.post(
            "/auth/forgot-password",
            json={"email": email},
            headers=headers_for(f"198.51.100.{i}"),
        )
        assert response.status_code == 204, response.text

    blocked = await client.post(
        "/auth/forgot-password",
        json={"email": email},
        headers=headers_for("198.51.100.200"),
    )
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0


@pytest.mark.asyncio
async def test_forgot_password_rejects_past_the_per_ip_limit(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
) -> None:
    """One host walking a list of addresses is stopped by the IP limit even
    though no single address is repeated."""
    client, _ = dispatched_emails

    for i in range(FORGOT_PASSWORD_IP_LIMIT.limit):
        response = await client.post(
            "/auth/forgot-password",
            json={"email": f"person-{i}@example.com"},
            headers=headers_for("203.0.113.9"),
        )
        assert response.status_code == 204, response.text

    blocked = await client.post(
        "/auth/forgot-password",
        json={"email": "one-more@example.com"},
        headers=headers_for("203.0.113.9"),
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
        for i in range(FORGOT_PASSWORD_EMAIL_LIMIT.limit + 1):
            response = await client.post(
                "/auth/forgot-password",
                json={"email": email},
                headers=headers_for(f"{ip_prefix}.{i}"),
            )
            codes.append(response.status_code)
        observed[label] = codes

    assert observed["real"] == observed["fake"]
    assert observed["real"][-1] == 429
    assert set(observed["real"][:-1]) == {204}


@pytest.mark.asyncio
async def test_forgot_password_spoofed_forwarded_header_cannot_dodge_the_ip_limit(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
) -> None:
    client, _ = dispatched_emails

    # Same real peer every time, rotating a spoofed value in front of it.
    for i in range(FORGOT_PASSWORD_IP_LIMIT.limit):
        response = await client.post(
            "/auth/forgot-password",
            json={"email": f"walk-{i}@example.com"},
            headers=headers_for(f"10.10.10.{i}, 203.0.113.77"),
        )
        assert response.status_code == 204, response.text

    blocked = await client.post(
        "/auth/forgot-password",
        json={"email": "walk-last@example.com"},
        headers=headers_for("10.10.10.254, 203.0.113.77"),
    )
    assert blocked.status_code == 429


@pytest.mark.asyncio
async def test_forgot_password_cooldown_suppresses_a_second_email_silently(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
    registered_user: Any,
) -> None:
    client, sent = dispatched_emails

    first = await client.post(
        "/auth/forgot-password",
        json={"email": registered_user.email},
        headers=headers_for("192.0.2.10"),
    )
    assert first.status_code == 204
    assert len(sent) == 1

    second = await client.post(
        "/auth/forgot-password",
        json={"email": registered_user.email},
        headers=headers_for("192.0.2.11"),
    )
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

    await client.post(
        "/auth/forgot-password",
        json={"email": registered_user.email},
        headers=headers_for("192.0.2.20"),
    )
    assert len(sent) == 1

    # Age the stored token past the cooldown rather than sleeping for it.
    from sqlmodel import col, select

    result = await test_session.execute(
        select(PasswordResetToken).where(
            col(PasswordResetToken.user_id) == registered_user.user_id
        )
    )
    token_row = result.scalars().one()
    token_row.created_at = now_est_naive() - timedelta(
        seconds=RESET_EMAIL_COOLDOWN_SECONDS + 5
    )
    test_session.add(token_row)
    await test_session.commit()

    again = await client.post(
        "/auth/forgot-password",
        json={"email": registered_user.email},
        headers=headers_for("192.0.2.21"),
    )
    assert again.status_code == 204
    assert len(sent) == 2


@pytest.mark.asyncio
async def test_forgot_password_cooldown_is_measured_on_the_stored_clock(
    test_session: AsyncSession, registered_user: Any
) -> None:
    """`created_at` is tz-naive local time. Measuring against a UTC now() would
    read as several hours old and never suppress anything."""
    service = get_password_reset_token_service()
    await service.create(test_session, registered_user.user_id)

    elapsed = await service.seconds_since_last_issued(
        test_session, registered_user.user_id
    )
    assert elapsed is not None
    assert 0 <= elapsed < 30, f"expected a just-created token, got {elapsed}s"


@pytest.mark.asyncio
async def test_seconds_since_last_issued_is_none_without_a_token(
    test_session: AsyncSession, registered_user: Any
) -> None:
    service = get_password_reset_token_service()
    assert (
        await service.seconds_since_last_issued(test_session, registered_user.user_id)
        is None
    )


@pytest.mark.asyncio
async def test_login_rejects_past_the_per_email_limit(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
) -> None:
    client, _ = dispatched_emails
    email = "target@example.com"

    codes = []
    for i in range(LOGIN_EMAIL_LIMIT.limit + 1):
        response = await client.post(
            "/auth/login",
            json={"email": email, "password": f"guess-{i}"},
            headers=headers_for(f"198.51.100.{i}"),
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
            "/auth/login",
            json={"email": f"user-{i}@example.com", "password": "whatever"},
            headers=headers_for("203.0.113.42"),
        )
        codes.append(response.status_code)

    assert codes[-1] == 429
    assert 429 not in codes[:-1], codes


@pytest.mark.asyncio
async def test_login_limit_is_not_swallowed_into_a_500(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
) -> None:
    """The handler wraps its body in `except Exception -> 500`; the limiter runs
    outside that block, so a 429 must survive as a 429."""
    client, _ = dispatched_emails

    for i in range(LOGIN_IP_LIMIT.limit):
        await client.post(
            "/auth/login",
            json={"email": f"user-{i}@example.com", "password": "whatever"},
            headers=headers_for("203.0.113.43"),
        )

    blocked = await client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "whatever"},
        headers=headers_for("203.0.113.43"),
    )
    assert blocked.status_code == 429
    assert blocked.headers.get("Retry-After") is not None


@pytest.mark.asyncio
async def test_validate_reset_token_is_rate_limited(
    dispatched_emails: tuple[AsyncClient, list[dict[str, Any]]],
) -> None:
    client, _ = dispatched_emails

    codes = []
    for _ in range(RESET_TOKEN_IP_LIMIT.limit + 1):
        response = await client.post(
            "/auth/validate-reset-token",
            json={"password_reset_token": "not-a-real-token"},
            headers=headers_for("203.0.113.51"),
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
            "/auth/update-password",
            json={
                "password_reset_token": "not-a-real-token",
                "new_password": "Str0ng!Passw0rd",
            },
            headers=headers_for("203.0.113.52"),
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
        response = await client.post(
            "/auth/refresh", headers=headers_for("203.0.113.60")
        )
        assert response.status_code != 429

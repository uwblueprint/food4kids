"""In-memory rate limiting for the unauthenticated auth endpoints.

Per-process counters: one uvicorn worker per Cloud Run instance, and Cloud Run
only adds instances under heavy concurrency, so this degrades to N x limit
rather than failing open. Redis is out of budget; a DB-backed limiter would turn
an attack into write load. The per-person email cap that must hold across
instances lives in `auth_routes._within_resend_cooldown` instead.
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

# So tests can reset every limiter between cases.
_ALL_LIMITERS: list["RateLimiter"] = []


@dataclass
class _Window:
    """A fixed window: when it opened, and how many requests landed in it."""

    started_at: float
    count: int


class RateLimiter:
    """Fixed-window request counter keyed by an arbitrary string.

    Allows up to 2x `limit` across a window boundary, which is fine here. Not
    thread-safe: `check` has no `await`, so call it from `async def` handlers
    only, where it runs atomically on the event loop.
    """

    def __init__(
        self,
        *,
        name: str,
        limit: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if limit < 1:
            raise ValueError(f"{name}: limit must be at least 1, got {limit}")
        if window_seconds <= 0:
            raise ValueError(
                f"{name}: window_seconds must be positive, got {window_seconds}"
            )

        self.name = name
        self.limit = limit
        self.window_seconds = window_seconds
        self._clock = clock  # injectable so tests can advance time
        self._windows: dict[str, _Window] = {}
        self._prune_at = 1024  # doubles after each prune: amortised O(1)

        _ALL_LIMITERS.append(self)

    def _drop_expired(self, now: float) -> None:
        expired = [
            key
            for key, window in self._windows.items()
            if now - window.started_at >= self.window_seconds
        ]
        for key in expired:
            del self._windows[key]

    def check(self, key: str) -> None:
        """Count one request against `key`; 429 + Retry-After once over the limit.

        Rejected requests do not extend the window, so hammering cannot lock a
        real user out indefinitely.
        """
        now = self._clock()
        window = self._windows.get(key)

        if window is None or now - window.started_at >= self.window_seconds:
            if len(self._windows) >= self._prune_at:
                self._drop_expired(now)
                self._prune_at = max(1024, 2 * len(self._windows))
            self._windows[key] = _Window(started_at=now, count=1)
            return

        window.count += 1
        if window.count > self.limit:
            if window.count == self.limit + 1:  # once per window, not per request
                logger.warning("Rate limit %s hit for %s", self.name, key)
            retry_after = int(self.window_seconds - (now - window.started_at)) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )

    def reset(self) -> None:
        """Forget all counters. Used by tests."""
        self._windows.clear()


def reset_all_rate_limiters() -> None:
    """Clear every limiter's state, so tests do not leak counts into each other."""
    for limiter in _ALL_LIMITERS:
        limiter.reset()


def client_ip(request: Request) -> str:
    """Client address from the RIGHTMOST X-Forwarded-For entry.

    Cloud Run appends the real peer and keeps anything the caller sent on the
    left (verified against a live echo service), so leftmost is spoofable.
    Assumes one proxy hop: a load balancer in front would need `hops[-2]`.
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        hops = [hop.strip() for hop in forwarded_for.split(",") if hop.strip()]
        if hops:
            return hops[-1]

    if request.client is not None:
        return request.client.host

    return "unknown"  # no peer at all: shared bucket rather than no limit


# Per-IP and per-email, since neither alone stops both a distributed attack on
# one person and one host walking a list. Loose enough for honest retries.

LOGIN_IP_LIMIT = RateLimiter(name="login-per-ip", limit=20, window_seconds=5 * 60)
LOGIN_EMAIL_LIMIT = RateLimiter(
    name="login-per-email", limit=10, window_seconds=15 * 60
)

# Shared by /forgot-password and /resend-onboarding: one budget of emails per
# person, whichever template.
EMAIL_SEND_IP_LIMIT = RateLimiter(
    name="email-send-per-ip", limit=15, window_seconds=60 * 60
)
# The 60s cooldown paces the button; this bounds the hourly total.
EMAIL_SEND_EMAIL_LIMIT = RateLimiter(
    name="email-send-per-email", limit=8, window_seconds=60 * 60
)

# Tokens are 32 random bytes, so this is hygiene rather than brute-force defence.
RESET_TOKEN_IP_LIMIT = RateLimiter(
    name="reset-token-per-ip", limit=20, window_seconds=15 * 60
)

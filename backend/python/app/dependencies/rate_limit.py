"""Rate limiting for the unauthenticated auth endpoints.

Nothing in this app was rate limited before, which meant anyone who knew a
volunteer's email address could call ``POST /auth/forgot-password`` in a loop to
mail-bomb that person and burn the project's email quota, and could spray
passwords at ``POST /auth/login`` unimpeded. The frontend's 60-second resend
countdown is client state only and does not constrain direct API calls.

**Why the counters live in process memory.** The backend runs one uvicorn worker
per Cloud Run instance, and Cloud Run only adds instances under heavy
concurrency. A per-instance counter therefore degrades to ``N x limit`` rather
than failing open -- and a rejected request costs well under a millisecond with
no database or email work, so an attacker needs a genuine DDoS to force a second
instance in the first place. The alternative that is correct across instances is
Redis, which does not fit this project's hosting budget (see the root CLAUDE.md
operating constraints), and a database-backed limiter would turn an attack into
write load on a small Postgres -- a worse failure mode than rejecting in memory.

**The one control that does not rely on this.** Capping *reset emails to a
specific person* is the thing we least want to leak across instances, so
``/auth/forgot-password`` also enforces a cooldown derived from the
``password_reset_tokens`` row it already writes. That is shared state for free,
with no new table. See ``RESET_EMAIL_COOLDOWN_SECONDS`` in ``auth_routes``.
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)

# Stop tracking new keys past this many live windows, so that a flood of
# distinct keys (spoofed IPs, random email addresses) cannot grow the map
# without bound. Entries are ~100 bytes, so this caps the limiter at a few MB.
# Reaching it means we are already under an attack large enough to be Cloud
# Run's problem rather than ours; existing keys stay limited, and the per-email
# cooldown in `/auth/forgot-password` is unaffected either way.
_MAX_TRACKED_KEYS = 20_000

# Every limiter constructed at import time, so tests can reset them between
# cases. Module-level counters would otherwise leak state across the suite.
_ALL_LIMITERS: list["RateLimiter"] = []


@dataclass
class _Window:
    """A fixed window: when it opened, and how many requests landed in it."""

    started_at: float
    count: int


class RateLimiter:
    """Fixed-window request counter keyed by an arbitrary string.

    Fixed windows (rather than a sliding log) keep this readable and allocate
    one small record per key. The known tradeoff is that a caller can land
    ``limit`` requests at the end of one window and ``limit`` more at the start
    of the next; for the abuse this defends against, a factor of two at the
    boundary does not matter.

    Not thread-safe by design: ``check`` contains no ``await``, so on the single
    uvicorn event loop it runs to completion without interleaving. Call it from
    ``async def`` handlers only -- a sync handler would run in a threadpool and
    could race.
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
        # Injectable purely so tests can advance time without sleeping. Defaults
        # to a monotonic clock, which (unlike wall time) cannot jump backwards
        # and hand out a free window on an NTP correction.
        self._clock = clock
        self._windows: dict[str, _Window] = {}

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
        """Record one request against ``key``.

        Raises 429 with a ``Retry-After`` header once the window's limit is
        exceeded. Requests that are rejected do not extend the window, so a
        caller who keeps hammering is let back in as soon as the window rolls
        over rather than being locked out indefinitely.
        """
        now = self._clock()
        window = self._windows.get(key)

        if window is None or now - window.started_at >= self.window_seconds:
            if len(self._windows) >= _MAX_TRACKED_KEYS:
                self._drop_expired(now)
            if len(self._windows) >= _MAX_TRACKED_KEYS:
                logger.warning(
                    "Rate limiter %s is tracking %d keys; not limiting new key",
                    self.name,
                    len(self._windows),
                )
                return
            self._windows[key] = _Window(started_at=now, count=1)
            return

        if window.count >= self.limit:
            retry_after = max(
                1, int(self.window_seconds - (now - window.started_at)) + 1
            )
            logger.warning(
                "Rate limit %s exceeded (%d in %.0fs); retry after %ds",
                self.name,
                window.count,
                self.window_seconds,
                retry_after,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )

        window.count += 1

    def reset(self) -> None:
        """Forget all counters. Used by tests."""
        self._windows.clear()


def reset_all_rate_limiters() -> None:
    """Clear every limiter's state, so tests do not leak counts into each other."""
    for limiter in _ALL_LIMITERS:
        limiter.reset()


def client_ip(request: Request) -> str:
    """Best-effort client address for rate-limiting purposes.

    ``request.client.host`` is Google's front end once deployed to Cloud Run, so
    using it directly would put every user of the app in a single bucket and let
    one abuser lock everybody out. The client address has to come from
    ``X-Forwarded-For`` instead.

    We take the **rightmost** entry. Proxies *append* to this header and do not
    validate what was already there, so any value a client sends for itself ends
    up on the left; trusting the leftmost entry is the classic bug that lets an
    attacker rotate a spoofed header and bypass a per-IP limit entirely. The
    rightmost entry is the one written by the infrastructure closest to us and
    cannot be forged by the caller.

    NOTE: this assumes exactly one proxy hop, which is the case for Cloud Run
    serving traffic directly. Putting a Google Cloud Load Balancer in front adds
    a hop, which would make the rightmost entry the balancer's address and once
    again collapse every user into one bucket. If that happens, this function
    needs to skip the extra hop -- the per-email limits below would still hold in
    the meantime.
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        hops = [hop.strip() for hop in forwarded_for.split(",") if hop.strip()]
        if hops:
            return hops[-1]

    if request.client is not None:
        return request.client.host

    # No peer address at all (can happen with synthetic ASGI scopes). Fall back
    # to a shared bucket rather than skipping the limit.
    return "unknown"


# ---------------------------------------------------------------------------
# Limits
#
# Two keys per endpoint, because neither alone is sufficient: a per-IP limit
# does not stop an attacker spread across hosts from targeting one person, and a
# per-email limit does not stop one host from walking a list of addresses.
#
# Values are deliberately loose enough that a volunteer mistyping a password or
# re-requesting a reset email will not hit them.
# ---------------------------------------------------------------------------

LOGIN_IP_LIMIT = RateLimiter(name="login-per-ip", limit=20, window_seconds=5 * 60)
LOGIN_EMAIL_LIMIT = RateLimiter(
    name="login-per-email", limit=10, window_seconds=15 * 60
)

FORGOT_PASSWORD_IP_LIMIT = RateLimiter(
    name="forgot-password-per-ip", limit=15, window_seconds=60 * 60
)
# Caps how many reset emails one address can trigger in an hour. The 60-second
# cooldown in `auth_routes` paces the resend button; this bounds the total, so a
# script that waits out the cooldown still cannot send 60 emails an hour.
FORGOT_PASSWORD_EMAIL_LIMIT = RateLimiter(
    name="forgot-password-per-email", limit=8, window_seconds=60 * 60
)

# Reset tokens are 32 random bytes, so these are not realistically brute
# forceable; the limit is cheap hygiene against someone hammering them.
RESET_TOKEN_IP_LIMIT = RateLimiter(
    name="reset-token-per-ip", limit=20, window_seconds=15 * 60
)

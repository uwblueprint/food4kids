"""Tests for which origins may make credentialed requests.

Every entry in ``allow_origins`` is trusted with the user's cookies, so the
cases worth pinning are the negative ones: what is *not* on the list.
"""

import pytest
from fastapi.testclient import TestClient

from app import create_app
from app.config import Environment, settings
from app.routers import API_PREFIX

UNKNOWN = "https://not-ours.example.com"
LOCALHOST = "http://localhost:3000"


def client(monkeypatch: pytest.MonkeyPatch, environment: Environment) -> TestClient:
    """An app built for ``environment``.

    Not used as a context manager on purpose: that would run the lifespan,
    which wants Firebase and a database. CORS is middleware, so it is wired
    by create_app() alone.
    """
    monkeypatch.setattr(settings, "environment", environment)
    return TestClient(create_app())


def allowed_origin(test_client: TestClient, origin: str) -> str | None:
    """The Access-Control-Allow-Origin a preflight from ``origin`` gets back."""
    response = test_client.options(
        f"{API_PREFIX}/auth/login",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
        },
    )
    allowed: str | None = response.headers.get("access-control-allow-origin")
    return allowed


class TestDevelopment:
    def test_localhost_is_allowed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        assert (
            allowed_origin(client(monkeypatch, Environment.DEVELOPMENT), LOCALHOST)
            == LOCALHOST
        )

    def test_loopback_by_ip_is_allowed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Vite prints both spellings; a developer opening either should work."""
        origin = "http://127.0.0.1:3000"
        assert (
            allowed_origin(client(monkeypatch, Environment.DEVELOPMENT), origin)
            == origin
        )

    def test_an_unknown_origin_is_refused(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        assert (
            allowed_origin(client(monkeypatch, Environment.DEVELOPMENT), UNKNOWN)
            is None
        )


class TestProduction:
    def test_localhost_is_not_allowed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The localhost entries are a development convenience and must not
        survive into a deployment, where they would let anything served from a
        victim's own machine make credentialed calls."""
        monkeypatch.setattr(settings, "cors_origins", [])
        assert (
            allowed_origin(client(monkeypatch, Environment.PRODUCTION), LOCALHOST)
            is None
        )

    def test_nothing_is_allowed_by_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "cors_origins", [])
        production = client(monkeypatch, Environment.PRODUCTION)
        for origin in (UNKNOWN, LOCALHOST, "https://food4kids-473501.web.app"):
            assert allowed_origin(production, origin) is None

    def test_a_configured_origin_is_allowed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        origin = "https://routes.food4kidswr.ca"
        monkeypatch.setattr(settings, "cors_origins", [origin])
        assert (
            allowed_origin(client(monkeypatch, Environment.PRODUCTION), origin)
            == origin
        )


class TestNoPatternsInAllowOrigins:
    """``allow_origins`` compares the Origin header by exact string.

    A pattern put there never matches anything — it is not a wildcard, it is a
    dead entry that reads like a working one. That is what the removed
    "https://uw-blueprint-starter-code--pr.*\\.web\\.app" line was. Patterns
    belong in ``allow_origin_regex``.
    """

    @pytest.mark.parametrize(
        "pattern", ["https://f4k--pr.*\\.web\\.app", "https://*.web.app"]
    )
    def test_a_pattern_matches_nothing(
        self, monkeypatch: pytest.MonkeyPatch, pattern: str
    ) -> None:
        monkeypatch.setattr(settings, "cors_origins", [pattern])
        assert (
            allowed_origin(
                client(monkeypatch, Environment.PRODUCTION),
                "https://f4k--pr123.web.app",
            )
            is None
        )

    def test_the_default_carries_no_patterns(self) -> None:
        for origin in settings.cors_origins:
            assert "*" not in origin, (
                f"{origin!r} looks like a pattern. allow_origins is an exact "
                "match; use allow_origin_regex instead."
            )

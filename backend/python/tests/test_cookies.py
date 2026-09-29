"""Refresh-cookie attributes per deployment.

The one combination browsers reject outright is SameSite=None without Secure:
the cookie is silently dropped and every session restore fails. Nothing here
may produce it.
"""

import itertools

import pytest
from fastapi import Response

from app.config import Environment, settings
from app.utilities.cookies import (
    clear_auth_cookies,
    get_cookie_options,
    set_refresh_token_cookie,
)

COMBINATIONS = list(itertools.product(Environment, (False, True)))


def configure(
    monkeypatch: pytest.MonkeyPatch, environment: Environment, preview: bool
) -> None:
    monkeypatch.setattr(settings, "environment", environment)
    monkeypatch.setattr(settings, "preview_deploy", preview)


def set_cookie_headers(response: Response) -> list[str]:
    return [v.decode() for k, v in response.raw_headers if k == b"set-cookie"]


@pytest.mark.parametrize(("environment", "preview"), COMBINATIONS)
def test_samesite_none_is_always_secure(
    monkeypatch: pytest.MonkeyPatch, environment: Environment, preview: bool
) -> None:
    configure(monkeypatch, environment, preview)
    options = get_cookie_options()
    assert options["httponly"] is True
    if options["samesite"] == "none":
        assert options["secure"] is True


class TestWhereEachDeploymentLands:
    def test_local_development_is_plain_http(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        configure(monkeypatch, Environment.DEVELOPMENT, preview=False)
        assert get_cookie_options() == {
            "httponly": True,
            "samesite": "strict",
            "secure": False,
        }

    def test_production_is_same_origin_and_secure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        configure(monkeypatch, Environment.PRODUCTION, preview=False)
        assert get_cookie_options() == {
            "httponly": True,
            "samesite": "strict",
            "secure": True,
        }

    @pytest.mark.parametrize("environment", list(Environment))
    def test_a_preview_deploy_is_cross_site_and_secure(
        self, monkeypatch: pytest.MonkeyPatch, environment: Environment
    ) -> None:
        configure(monkeypatch, environment, preview=True)
        assert get_cookie_options() == {
            "httponly": True,
            "samesite": "none",
            "secure": True,
        }


class TestTheHeadersCarryTheOptions:
    @pytest.mark.parametrize(("environment", "preview"), COMBINATIONS)
    @pytest.mark.parametrize("remember_me", (False, True))
    def test_set(
        self,
        monkeypatch: pytest.MonkeyPatch,
        environment: Environment,
        preview: bool,
        remember_me: bool,
    ) -> None:
        configure(monkeypatch, environment, preview)
        response = Response()
        set_refresh_token_cookie(response, "tok", remember_me)
        headers = set_cookie_headers(response)
        assert sorted(h.split("=", 1)[0] for h in headers) == [
            "refreshToken",
            "rememberMe",
        ]
        for header in headers:
            assert "HttpOnly" in header
            assert f"SameSite={get_cookie_options()['samesite']}" in header
            assert ("Secure" in header) is bool(get_cookie_options()["secure"])
            assert ("Max-Age=" in header) is remember_me

    @pytest.mark.parametrize(("environment", "preview"), COMBINATIONS)
    def test_clear(
        self, monkeypatch: pytest.MonkeyPatch, environment: Environment, preview: bool
    ) -> None:
        configure(monkeypatch, environment, preview)
        response = Response()
        clear_auth_cookies(response)
        headers = set_cookie_headers(response)
        assert sorted(h.split("=", 1)[0] for h in headers) == [
            "refreshToken",
            "rememberMe",
        ]
        for header in headers:
            assert "Max-Age=0" in header
            assert ("Secure" in header) is bool(get_cookie_options()["secure"])

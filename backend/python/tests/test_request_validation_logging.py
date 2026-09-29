"""Contract for the app-wide 422 handler.

A validation failure is resolved before any route handler runs, so until
:func:`~app.middleware.log_request_validation_error` was wired in it produced no
log line at all — the caller was told which fields were wrong and the server
side stayed silent (see #242).

These tests pin the two halves of that fix: the failure has to reach the log
with enough detail to act on, and it must not drag the submitted values along
with it.
"""

import logging

import pytest
from fastapi import APIRouter, status
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from app import create_app
from app.config import settings

LOGGER_NAME = "app.middleware"

ALLOWED_ORIGIN = "http://localhost:3000"

# Stands in for the household data these endpoints really carry: if a value like
# this can reach the log, so can a real family's address.
SENSITIVE_VALUE = "417 Erb St W, Waterloo — guardian Priya Raman, 3 children"

probe_router = APIRouter(prefix="/_probe")


class Household(BaseModel):
    address: str
    num_children: int


@probe_router.post("/household")
async def probe_household(household: Household) -> dict[str, int]:
    return {"num_children": household.num_children}


@pytest.fixture
def probe_client(monkeypatch: pytest.MonkeyPatch) -> AsyncClient:
    """A client for the real app, with a route that validates a body.

    Built from ``create_app`` so the handler under test is the one the app
    actually registers, rather than a hand-wired copy.

    ALLOWED_ORIGIN is configured here rather than inherited from the default
    list, so the CORS assertions below test middleware ordering and not which
    origins happen to ship enabled.
    """
    monkeypatch.setattr(settings, "cors_origins", [ALLOWED_ORIGIN])
    app = create_app()
    app.include_router(probe_router)
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


class TestValidationFailureIsLogged:
    @pytest.mark.asyncio
    async def test_missing_fields_are_named_in_the_log(
        self, probe_client: AsyncClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The log has to say *which* fields, or it cannot end the debugging."""
        with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
            async with probe_client as client:
                await client.post("/_probe/household", json={})

        (record,) = [r for r in caplog.records if r.name == LOGGER_NAME]
        message = record.getMessage()
        assert "POST" in message
        assert "/_probe/household" in message
        assert "body.address" in message
        assert "body.num_children" in message

    @pytest.mark.asyncio
    async def test_wrong_type_is_logged(
        self, probe_client: AsyncClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
            async with probe_client as client:
                await client.post(
                    "/_probe/household",
                    json={"address": "1 King St", "num_children": "lots"},
                )

        (record,) = [r for r in caplog.records if r.name == LOGGER_NAME]
        assert "body.num_children" in record.getMessage()

    @pytest.mark.asyncio
    async def test_logged_at_warning_not_error(
        self, probe_client: AsyncClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A malformed request is the caller's bug, not an outage."""
        with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
            async with probe_client as client:
                await client.post("/_probe/household", json={})

        (record,) = [r for r in caplog.records if r.name == LOGGER_NAME]
        assert record.levelno == logging.WARNING

    @pytest.mark.asyncio
    async def test_a_valid_request_logs_nothing(
        self, probe_client: AsyncClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
            async with probe_client as client:
                response = await client.post(
                    "/_probe/household",
                    json={"address": "1 King St", "num_children": 2},
                )

        assert response.status_code == status.HTTP_200_OK
        assert [r for r in caplog.records if r.name == LOGGER_NAME] == []


class TestSubmittedValuesStayOutOfTheLog:
    """pydantic returns the offending value under ``input``; it must not be logged.

    These endpoints carry household addresses, phone numbers and children's
    names. A 422 body goes to an authenticated admin over TLS, but container
    logs are a different audience with a different retention story.
    """

    @pytest.mark.asyncio
    async def test_offending_value_is_not_logged(
        self, probe_client: AsyncClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
            async with probe_client as client:
                await client.post(
                    "/_probe/household",
                    json={"address": SENSITIVE_VALUE, "num_children": "lots"},
                )

        assert SENSITIVE_VALUE not in caplog.text

    @pytest.mark.asyncio
    async def test_valid_sibling_fields_are_not_logged(
        self, probe_client: AsyncClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The value that *passed* validation is just as sensitive as the one
        that failed, and has even less reason to be echoed."""
        with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
            async with probe_client as client:
                await client.post(
                    "/_probe/household", json={"address": SENSITIVE_VALUE}
                )

        assert SENSITIVE_VALUE not in caplog.text


class TestResponseIsUnchanged:
    """Logging is additive: the 422 body is FastAPI's, and stays FastAPI's.

    The generated TypeScript client and the OpenAPI schema both describe this
    shape, so rebuilding the response here would let it drift.
    """

    @pytest.mark.asyncio
    async def test_status_and_body_shape_are_fastapis(
        self, probe_client: AsyncClient
    ) -> None:
        async with probe_client as client:
            response = await client.post("/_probe/household", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        detail = response.json()["detail"]
        assert isinstance(detail, list)
        assert {tuple(error["loc"]) for error in detail} == {
            ("body", "address"),
            ("body", "num_children"),
        }
        assert all(error["type"] == "missing" for error in detail)

    @pytest.mark.asyncio
    async def test_422_carries_cors_headers(self, probe_client: AsyncClient) -> None:
        """Registered inside CORS, like the 500 path — a browser cannot read an
        error response that arrives without the header."""
        async with probe_client as client:
            response = await client.post(
                "/_probe/household", json={}, headers={"Origin": ALLOWED_ORIGIN}
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN

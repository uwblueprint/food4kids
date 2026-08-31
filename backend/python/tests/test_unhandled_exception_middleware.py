"""Contract for the app-wide 500 handler.

Route handlers no longer wrap their bodies in ``except Exception``.
:class:`~app.middleware.UnhandledExceptionMiddleware` is what turns an
unexpected failure into a 500 now, and these tests pin the three things the
per-handler version got wrong (see #216): a deliberate ``HTTPException`` must
survive, the response body must not carry internal error text, and the
traceback must actually reach the log.
"""

import ast
import logging
import pathlib
from collections.abc import AsyncIterator

import pytest
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from httpx import ASGITransport, AsyncClient

from app import create_app
from app.config import settings

SECRET = "connection to 10.0.0.7 refused: password authentication failed"

ALLOWED_ORIGIN = "http://localhost:3000"

probe_router = APIRouter(prefix="/_probe")


@probe_router.get("/boom")
async def probe_boom() -> None:
    raise RuntimeError(SECRET)


@probe_router.get("/ok")
async def probe_ok() -> dict[str, str]:
    return {"status": "ok"}


@probe_router.get("/teapot")
async def probe_teapot() -> None:
    raise HTTPException(status_code=418, detail="deliberate")


@probe_router.get("/value-error")
async def probe_value_error() -> None:
    raise ValueError(SECRET)


@probe_router.get("/stream-boom")
async def probe_stream_boom() -> StreamingResponse:
    async def body() -> AsyncIterator[bytes]:
        yield b"first chunk"
        raise RuntimeError(SECRET)

    return StreamingResponse(body(), media_type="text/plain")


@pytest.fixture
def probe_client(monkeypatch: pytest.MonkeyPatch) -> AsyncClient:
    """A client for the real app, with routes that fail on demand bolted on.

    Built from ``create_app`` rather than a hand-rolled FastAPI instance so the
    middleware *ordering* is the one the app actually ships.

    ALLOWED_ORIGIN is configured here rather than inherited from the default
    list, so the CORS assertions below test middleware ordering and not which
    origins happen to ship enabled.
    """
    monkeypatch.setattr(settings, "cors_origins", [ALLOWED_ORIGIN])
    app = create_app()
    app.include_router(probe_router)
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


class TestUnhandledExceptions:
    @pytest.mark.asyncio
    async def test_unexpected_error_becomes_a_500(
        self, probe_client: AsyncClient
    ) -> None:
        async with probe_client as client:
            response = await client.get("/_probe/boom")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == {"detail": "Internal server error"}

    @pytest.mark.asyncio
    @pytest.mark.parametrize("path", ["/_probe/boom", "/_probe/value-error"])
    async def test_500_body_never_leaks_the_exception_text(
        self, probe_client: AsyncClient, path: str
    ) -> None:
        """``detail=str(e)`` used to hand internal error text to the caller."""
        async with probe_client as client:
            response = await client.get(path)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert SECRET not in response.text

    @pytest.mark.asyncio
    async def test_traceback_is_logged(
        self, probe_client: AsyncClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Re-raising as ``HTTPException`` made the failure look expected to
        Starlette, so nothing ever logged it."""
        with caplog.at_level(logging.ERROR, logger="app.middleware"):
            async with probe_client as client:
                await client.get("/_probe/boom")

        (record,) = [r for r in caplog.records if r.name == "app.middleware"]
        assert record.exc_info is not None
        assert SECRET in caplog.text
        assert "GET" in record.getMessage()
        assert "/_probe/boom" in record.getMessage()

    @pytest.mark.asyncio
    async def test_deliberate_http_error_is_untouched(
        self, probe_client: AsyncClient
    ) -> None:
        """The #216 bug: a handler's own 4xx must not be rewritten as a 500."""
        async with probe_client as client:
            response = await client.get("/_probe/teapot")

        assert response.status_code == 418
        assert response.json() == {"detail": "deliberate"}

    @pytest.mark.asyncio
    async def test_successful_request_is_unaffected(
        self, probe_client: AsyncClient
    ) -> None:
        async with probe_client as client:
            response = await client.get("/_probe/ok")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_500_carries_cors_headers(self, probe_client: AsyncClient) -> None:
        """The middleware must sit *inside* CORS.

        Outside it (which is where ``add_exception_handler(Exception, ...)``
        puts you) the 500 ships without ``Access-Control-Allow-Origin``, and a
        browser reports an opaque CORS failure instead of the error.
        """
        async with probe_client as client:
            response = await client.get(
                "/_probe/boom", headers={"Origin": ALLOWED_ORIGIN}
            )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN

    @pytest.mark.asyncio
    async def test_failure_mid_stream_is_not_swallowed(
        self, probe_client: AsyncClient
    ) -> None:
        """Once the response has started the status line is already sent, so
        there is no 500 to substitute — the error must propagate rather than
        be quietly dropped."""
        with pytest.raises(RuntimeError, match="refused"):
            async with probe_client as client:
                await client.get("/_probe/stream-boom")


class TestNoBlanketHandlersRemain:
    """Structural guard: the pattern itself must not come back.

    A blanket ``except Exception`` that raises its own 500 re-introduces all
    three failure modes at once, and the next one added will not have a test of
    its own. Catching an exception to do real cleanup and then re-raising is
    fine — it is *converting* it to a 500 that this forbids.
    """

    @staticmethod
    def _blanket_500_handlers(path: pathlib.Path) -> list[int]:
        tree = ast.parse(path.read_text())
        found = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue
            for handler in node.handlers:
                if handler.type is None or ast.unparse(handler.type) != "Exception":
                    continue
                raises = [
                    ast.unparse(n.exc)
                    for n in ast.walk(handler)
                    if isinstance(n, ast.Raise) and n.exc is not None
                ]
                if any(
                    "500_INTERNAL_SERVER_ERROR" in r or "status_code=500" in r
                    for r in raises
                ):
                    found.append(handler.lineno)
        return found

    def test_nothing_in_app_raises_a_500_from_a_broad_except(self) -> None:
        app_dir = pathlib.Path(__file__).parent.parent / "app"
        offenders = {
            str(path.relative_to(app_dir)): lines
            for path in sorted(app_dir.rglob("*.py"))
            if (lines := self._blanket_500_handlers(path))
        }
        assert offenders == {}, (
            "Let unexpected errors reach UnhandledExceptionMiddleware, which "
            "logs the traceback and returns a 500 that leaks nothing, instead "
            f"of raising your own: {offenders}"
        )

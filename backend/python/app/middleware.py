"""How a failed request becomes a response, wired up in :func:`app.create_app`.

Two paths, at opposite ends of the request: :class:`UnhandledExceptionMiddleware`
catches what a route handler raised, and :func:`log_request_validation_error`
catches what never reached one.
"""

import logging
from collections.abc import Sequence
from typing import Any

from fastapi import Request, status
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)


class UnhandledExceptionMiddleware:
    """Log the traceback of an unhandled exception, answer with a bare 500.

    So handlers need no catch-all ``except Exception`` of their own — that
    swallowed the ``HTTPException`` they had just raised and leaked internal
    error text through ``detail``. Keep only specific ``except`` clauses that
    map a known failure to a meaningful 4xx.

    Wired inside the CORS layer, so the 500 still carries the headers a browser
    needs to read it. Once the response has started there is nothing left to
    change, and the exception goes on to Starlette.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            logger.exception(
                "Unhandled exception on %s %s",
                scope.get("method", "?"),
                scope.get("path", "?"),
            )
            if response_started:
                raise
            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"},
            )
            await response(scope, receive, send)


def _describe(errors: Sequence[Any]) -> str:
    """Render where each error is and what it is — never the value that caused it."""
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc']) or '<request>'}: {error['msg']}"
        for error in errors
    )


async def log_request_validation_error(request: Request, exc: Exception) -> Response:
    """Log a 422 on its way out, then let FastAPI answer it as it always has.

    FastAPI rejects a malformed request while resolving the route's parameters,
    before any handler body runs, so without this a 422 leaves no server-side
    trace at all — only the caller is told what was wrong. The response is
    delegated rather than rebuilt so its shape can't drift from FastAPI's.
    """
    if not isinstance(exc, RequestValidationError):  # pragma: no cover - defensive
        raise exc

    logger.warning(
        "Request validation failed on %s %s — %s",
        request.method,
        request.url.path,
        _describe(exc.errors()),
    )
    return await request_validation_exception_handler(request, exc)

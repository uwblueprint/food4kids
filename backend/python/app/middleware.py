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
    """Turn an unhandled exception into a 500 that says nothing about it.

    Route handlers deliberately do *not* wrap their bodies in
    ``except Exception``. Doing so per-handler cost us three things:

    1. ``HTTPException`` subclasses ``Exception``, so a handler caught the
       4xx it had just raised and re-emitted it as a 500 (see #216).
    2. ``detail=str(e)`` leaked internal error text — SQL, constraint names,
       third-party client messages — to whoever called the endpoint.
    3. Re-raising as ``HTTPException`` made the failure look *expected* to
       Starlette, so the original traceback was never logged.

    This middleware sits inside the CORS layer (so the 500 still carries the
    CORS headers a browser needs to read it) and outside the router, and
    handles all three centrally: it logs the traceback and returns a fixed
    body. Handlers keep only their specific ``except`` clauses, which map a
    known failure to a meaningful 4xx.

    If the response has already started, the body is committed and the status
    line is long gone, so there is nothing to salvage — the exception is
    re-raised for Starlette's ``ServerErrorMiddleware`` to deal with.
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
    which is *before* any handler body runs. Nothing downstream of that point
    ever executes, so a 422 leaves no trace: the caller is told which fields are
    missing, and the server log shows the request never happened. Debugging one
    means reproducing it with a network tab open, because the logs cannot help.

    That combination cost a long session on #242, where the frontend was posting
    JSON to a multipart endpoint. The server knew exactly what was wrong with the
    request and said so only to the caller.

    Only the *shape* of each error is logged — its location and message. The
    ``input`` key that pydantic also returns echoes the submitted value back, and
    these endpoints carry household addresses, phone numbers and children's
    names; that belongs in a 422 body going to an authenticated admin, not in
    container logs. The response itself is delegated rather than rebuilt, so the
    contract the frontend and OpenAPI schema depend on cannot drift from here.
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

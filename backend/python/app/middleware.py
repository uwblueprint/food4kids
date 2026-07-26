"""ASGI middleware wired into the app in :func:`app.create_app`."""

import logging

from fastapi import status
from fastapi.responses import JSONResponse
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

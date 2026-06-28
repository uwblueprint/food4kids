from typing import Literal, cast
from fastapi import Response
from app.config import settings

# Refresh tokens last 14 days
REFRESH_TOKEN_MAX_AGE = 14 * 24 * 60 * 60

def get_cookie_options() -> dict[str, bool | Literal["none", "strict", "lax"]]:
    """Get cookie options based on environment"""
    samesite: Literal["none", "strict", "lax"] = (
        "none" if settings.preview_deploy else "strict"
    )
    return {
        "httponly": True,
        "samesite": samesite,
        "secure": settings.is_production,
    }

def set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    """
    Sets the HTTP-only refresh token cookie on the response object
    with a robust expiration date.
    """
    cookie_options = get_cookie_options()
    
    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=bool(cookie_options["httponly"]),
        samesite=cast(
            Literal["none", "strict", "lax"], cookie_options["samesite"]
        ),
        secure=bool(cookie_options["secure"]),
        max_age=REFRESH_TOKEN_MAX_AGE,
    )

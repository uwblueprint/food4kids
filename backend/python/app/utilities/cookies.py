from typing import Literal

from app.config import settings


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

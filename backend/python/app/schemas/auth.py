from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.driver import DriverRead


class LoginRequest(BaseModel):
    """Login request"""

    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Authentication response"""

    access_token: str
    id: UUID
    name: str
    email: EmailStr


class DriverRegisterResponse(BaseModel):
    """Driver registration response - contains Driver object and AuthResponse"""

    driver: DriverRead
    auth: AuthResponse


class TokenResponse(BaseModel):
    """Token response from Firebase API - contains both tokens for internal use"""

    access_token: str
    refresh_token: str


class RefreshResponse(BaseModel):
    """Refresh token response - only access token, refresh token is set as httpOnly cookie"""

    access_token: str

from pydantic import BaseModel, EmailStr

from app.models.enum import RoleEnum


class LoginRequest(BaseModel):
    """Login request"""

    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Authentication response"""

    access_token: str
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: RoleEnum


class TokenResponse(BaseModel):
    """Token response from Firebase API - contains both tokens for internal use"""

    access_token: str
    refresh_token: str


class RefreshResponse(BaseModel):
    """Refresh token response - only access token, refresh token is set as httpOnly cookie"""

    access_token: str

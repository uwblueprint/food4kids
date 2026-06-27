from uuid import UUID

from pydantic import BaseModel, EmailStr, computed_field, Field

from app.models.driver import DriverRead


class LoginRequest(BaseModel):
    """Login request"""

    email: EmailStr
    password: str
    

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class UpdatePasswordRequest(BaseModel):
    password_reset_token: str
    new_password: str = Field(min_length=8, max_length=100)

class AuthResponse(BaseModel):
    """Authentication response"""

    access_token: str
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr

    @computed_field  # type: ignore[prop-decorator]
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


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

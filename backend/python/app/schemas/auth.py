from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, computed_field, field_validator

from app.utilities.utils import validate_password_complexity


class LoginRequest(BaseModel):
    """Login request"""

    email: EmailStr
    password: str
    remember_me: bool = False


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ValidateResetTokenRequest(BaseModel):
    password_reset_token: str


class UpdatePasswordRequest(BaseModel):
    password_reset_token: str
    new_password: str = Field(min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def check_password(cls, password: str) -> str:
        return validate_password_complexity(password)


class AuthResponse(BaseModel):
    """Authentication response"""

    access_token: str
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    role: str
    remember_me: bool
    driver_id: UUID | None = None
    admin_id: UUID | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class TokenResponse(BaseModel):
    """Token response from Firebase API - contains both tokens for internal use"""

    access_token: str
    refresh_token: str

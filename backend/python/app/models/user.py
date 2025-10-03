from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from .base import BaseModel
from .enum import RoleEnum


class UserBase(SQLModel):
    """Shared fields between table and API models"""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr = Field(unique=True, index=True)
    role: RoleEnum = Field(default=RoleEnum.USER)


class User(UserBase, BaseModel, table=True):
    """Database table model"""

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    auth_id: str = Field(nullable=False, unique=True, index=True)


class UserCreate(UserBase):
    """Create request model"""

    password: str = Field(min_length=8, max_length=100)


class UserRead(UserBase):
    """Read response model"""

    id: int
    auth_id: str


class UserUpdate(SQLModel):
    """Update request model - all optional"""

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = Field(default=None)
    role: RoleEnum | None = Field(default=None)


class UserRegister(SQLModel):
    """User registration request"""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)

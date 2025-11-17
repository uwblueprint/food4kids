from uuid import UUID, uuid4

from pydantic import EmailStr, field_validator
from sqlmodel import Field, SQLModel

from .base import BaseModel


class UserBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(unique=True, index=True, max_length=254)


class User(UserBase, BaseModel, table=True):
    __tablename__ = "users"

    user_id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    auth_id: str = Field(nullable=False, unique=True, index=True)
    role: str = Field(min_length=1, max_length=255, default="driver")


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=100)


class UserRead(UserBase):
    user_id: UUID
    auth_id: str
    role: str


class UserUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=254)

class UserRegister(SQLModel):
    """User registration request"""

    name: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=8, max_length=100)

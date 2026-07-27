from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from pydantic import EmailStr, computed_field
from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .driver import Driver


class UserBase(SQLModel):
    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(unique=True, index=True, max_length=254)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class User(UserBase, BaseModel, table=True):
    __tablename__ = "users"

    user_id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    auth_id: str | None = Field(nullable=True, unique=True, index=True)
    role: str = Field(min_length=1, max_length=255, default="driver")

    driver: Optional["Driver"] = Relationship(
        back_populates="user", cascade_delete=True
    )


class UserRead(UserBase):
    user_id: UUID
    auth_id: str | None
    role: str


class UserUpdate(SQLModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=255)
    last_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=254)


class UserFinalize(SQLModel):
    user_invite_id: UUID
    password: str = Field(min_length=8, max_length=100)

from uuid import UUID, uuid4

from pydantic import EmailStr, field_validator
from sqlmodel import Field, Relationship, SQLModel

from app.models.user import User
from app.utilities.utils import validate_phone

from .base import BaseModel


class AdminBase(SQLModel):
    """Shared fields between table and API models"""

    receive_email_notifications: bool = Field(default=True, nullable=False)
    admin_phone: str = Field(min_length=1, max_length=100, nullable=False)

    @field_validator("admin_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number using phonenumbers library"""
        return validate_phone(v)


class Admin(AdminBase, BaseModel, table=True):
    """Database table model"""

    __tablename__ = "admin_info"

    admin_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(
        foreign_key="users.user_id", unique=True, nullable=False, ondelete="CASCADE"
    )

    user: User = Relationship()


class AdminCreate(AdminBase):
    """Create request model"""

    user_id: UUID
    pass


class AdminRead(AdminBase):
    """Read response model"""

    admin_id: UUID
    user_id: UUID

    # pulled from User
    name: str
    email: EmailStr
    auth_id: str
    role: str


class AdminUpdate(SQLModel):
    """Update request model - all optional"""

    # admin-specific
    admin_phone: str | None = Field(default=None, min_length=1, max_length=100)

    # user fields
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = Field(default=None)

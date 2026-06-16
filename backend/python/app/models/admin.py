from uuid import UUID, uuid4

from pydantic import EmailStr, computed_field, field_validator
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
    first_name: str
    last_name: str
    email: EmailStr
    auth_id: str
    role: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class AdminUpdate(SQLModel):
    """Update request model - all optional"""

    # admin-specific
    admin_phone: str | None = Field(default=None, min_length=1, max_length=100)

    # user fields
    first_name: str | None = Field(default=None, min_length=1, max_length=255)
    last_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = Field(default=None)

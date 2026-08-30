from uuid import UUID, uuid4

from pydantic import EmailStr, computed_field, field_validator
from sqlmodel import Field, Relationship, SQLModel

from app.models.user import User
from app.utilities.utils import validate_phone

from .base import BaseModel


class AdminBase(SQLModel):
    """Shared fields between table and API models"""

    receive_email_notifications: bool = Field(default=True, nullable=False)
    # Optional: an admin bootstrapped from the CLI may not have a number on
    # file, and inventing a placeholder to satisfy a NOT NULL would be worse
    # than storing nothing. Same treatment as the driver columns.
    admin_phone: str | None = Field(default=None, max_length=100)

    @field_validator("admin_phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """Validate the number when there is one; absence is allowed.

        An empty string means "no number", not "a phone that passes
        validation" — it normalizes to NULL rather than being stored as ''.
        """
        return validate_phone(v) if v else None


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
    # The column is nullable now, so an explicit ``null`` is a legitimate
    # "clear this number" rather than something to reject — the guard that used
    # to turn it into a 422 is gone, matching how DriverUpdate treats phone.
    admin_phone: str | None = Field(default=None, max_length=100)

    @field_validator("admin_phone")
    @classmethod
    def validate_admin_phone(cls, v: str | None) -> str | None:
        """Normalize on update too — the service assigns straight onto the row,
        and SQLModel table instances don't re-run validators on assignment, so
        without this an edit writes whatever string the client sent."""
        return validate_phone(v) if v else None

    # user fields
    first_name: str | None = Field(default=None, min_length=1, max_length=255)
    last_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = Field(default=None)

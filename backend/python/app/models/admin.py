from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from .base import BaseModel


class AdminBase(SQLModel):
    """Shared fields between table and API models"""

    admin_name: str = Field(min_length=1, max_length=100, nullable=False)
    default_cap: int | None = Field(default=None)
    admin_phone: str = Field(min_length=1, max_length=100, nullable=False)
    admin_email: EmailStr = Field(nullable=False)
    route_start_time: str | None = Field(default=None)
    warehouse_location: str | None = Field(default=None, min_length=1)
    preferred_language: str | None = Field(default=None)
    admin_timezone: str | None = Field(default=None)


class Admin(AdminBase, BaseModel, table=True):
    """Database table model"""

    __tablename__ = "admin_info"

    admin_id: UUID = Field(default_factory=uuid4, primary_key=True)


class AdminCreate(AdminBase):
    """Create request model"""

    pass


class AdminRead(AdminBase):
    """Read response model"""

    admin_id: UUID


class AdminUpdate(SQLModel):
    """Update request model - all optional"""

    admin_name: str | None = Field(default=None, min_length=1, max_length=100)
    default_cap: int | None = Field(default=None)
    admin_phone: str | None = Field(default=None, min_length=1, max_length=100)
    admin_email: EmailStr | None = Field(default=None)
    route_start_time: str | None = Field(default=None)
    warehouse_location: str | None = Field(default=None, min_length=1)
    preferred_language: str | None = Field(default=None)
    admin_timezone: str | None = Field(default=None)


class AdminRegister(SQLModel):
    """Admin registration request"""

    admin_name: str = Field(min_length=1, max_length=100)
    admin_phone: str = Field(min_length=1, max_length=100)
    admin_email: EmailStr
    admin_password: str = Field(min_length=8, max_length=100)

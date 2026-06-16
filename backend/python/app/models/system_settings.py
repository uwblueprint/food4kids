import datetime
from uuid import UUID, uuid4

from pydantic import EmailStr, field_validator
from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel

from app.utilities.utils import validate_phone

from .base import BaseModel


class SystemSettingsBase(SQLModel):
    """Shared fields between table and API models"""

    default_cap: int | None = Field(default=None)
    route_start_time: datetime.time | None = Field(default=None)
    warehouse_location: str | None = Field(default=None, min_length=1)
    warehouse_longitude: float | None = None
    warehouse_latitude: float | None = None
    import_column_map: dict[str, str] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    boxes_per_car: int = Field(default=10, ge=0)
    dropoff_minutes: int = Field(default=3, ge=0)
    children_per_box: int = Field(default=2, ge=0)
    contact_name: str | None = Field(default=None, min_length=1, max_length=255)
    contact_phone: str | None = Field(default=None, min_length=1, max_length=100)
    f4k_wr_instagram: str | None = Field(default=None, min_length=1, max_length=255)
    f4k_wr_facebook: str | None = Field(default=None, min_length=1, max_length=255)
    f4k_wr_email: EmailStr | None = Field(default=None)
    f4k_wr_website: str | None = Field(default=None, min_length=1, max_length=255)
    f4k_wr_address: str | None = Field(default=None, min_length=1, max_length=255)
    email_reminder_days_before: list[int] = Field(
        default_factory=lambda: [1], sa_column=Column(JSON, nullable=False)
    )
    email_reminder_time: datetime.time = Field(
        default=datetime.time(9, 0, 0), nullable=False
    )

    @field_validator("contact_phone")
    @classmethod
    def validate_contact_phone(cls, v: str | None) -> str | None:
        """Validate the contact phone number when configured."""
        if v is None:
            return None
        return validate_phone(v)


class SystemSettings(SystemSettingsBase, BaseModel, table=True):
    """Database table model"""

    __tablename__ = "system_settings"

    system_settings_id: UUID = Field(default_factory=uuid4, primary_key=True)


class SystemSettingsCreate(SystemSettingsBase):
    """Create request model"""

    pass


class SystemSettingsRead(SystemSettingsBase):
    """Read response model"""

    system_settings_id: UUID


class SystemSettingsUpdate(SQLModel):
    """Update request model - all optional"""

    default_cap: int | None = Field(default=None)
    route_start_time: datetime.time | None = Field(default=None)
    warehouse_location: str | None = Field(default=None, min_length=1)
    warehouse_longitude: float | None = None
    warehouse_latitude: float | None = None
    import_column_map: dict[str, str] | None = Field(default=None)
    boxes_per_car: int | None = Field(default=None, ge=0)
    dropoff_minutes: int | None = Field(default=None, ge=0)
    children_per_box: int | None = Field(default=None, ge=0)
    contact_name: str | None = Field(default=None, min_length=1, max_length=255)
    contact_phone: str | None = Field(default=None, min_length=1, max_length=100)
    f4k_wr_instagram: str | None = Field(default=None, min_length=1, max_length=255)
    f4k_wr_facebook: str | None = Field(default=None, min_length=1, max_length=255)
    f4k_wr_email: EmailStr | None = Field(default=None)
    f4k_wr_website: str | None = Field(default=None, min_length=1, max_length=255)
    f4k_wr_address: str | None = Field(default=None, min_length=1, max_length=255)
    email_reminder_days_before: list[int] | None = Field(default=None)
    email_reminder_time: datetime.time | None = Field(default=None)

    @field_validator("contact_phone")
    @classmethod
    def validate_contact_phone(cls, v: str | None) -> str | None:
        """Validate the contact phone number when configured."""
        if v is None:
            return None
        return validate_phone(v)

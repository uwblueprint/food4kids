import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import EmailStr, field_validator
from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator
from sqlmodel import Column, Field, SQLModel

from app.utilities.utils import validate_phone

from .base import BaseModel


class EmailReminder(SQLModel):
    """A single reminder email configuration.

    Each reminder fires ``days_before`` days ahead of a route's drive date, at its
    own ``time`` — so admins can set, e.g., a day-before reminder at 9 AM and a
    same-day reminder at 11 AM.
    """

    days_before: int = Field(ge=0)
    time: datetime.time


class EmailReminderListType(TypeDecorator[list[EmailReminder]]):
    """Persist ``list[EmailReminder]`` in a JSON column.

    The stdlib JSON serializer can't encode ``datetime.time``, so each reminder is
    round-tripped through pydantic's JSON-mode dump (``time`` -> ``"HH:MM:SS"``)
    when binding and re-validated when loading.
    """

    impl = JSON
    cache_ok = True

    def process_bind_param(
        self, value: list[EmailReminder] | None, _dialect: Any
    ) -> list[dict[str, Any]] | None:
        if value is None:
            return None
        return [EmailReminder.model_validate(r).model_dump(mode="json") for r in value]

    def process_result_value(
        self, value: Any, _dialect: Any
    ) -> list[EmailReminder] | None:
        if value is None:
            return None
        return [EmailReminder.model_validate(r) for r in value]


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
    # Must be >= 1: box counts are derived as ceil(num_children / children_per_box),
    # so a zero divisor is invalid (see app.utilities.boxes.compute_boxes).
    children_per_box: int = Field(default=2, ge=1)
    contact_name: str | None = Field(default=None, min_length=1, max_length=255)
    contact_phone: str | None = Field(default=None, min_length=1, max_length=100)
    f4k_wr_instagram: str | None = Field(default=None, min_length=1, max_length=255)
    f4k_wr_facebook: str | None = Field(default=None, min_length=1, max_length=255)
    f4k_wr_email: EmailStr | None = Field(default=None)
    f4k_wr_website: str | None = Field(default=None, min_length=1, max_length=255)
    f4k_wr_address: str | None = Field(default=None, min_length=1, max_length=255)
    email_reminders: list[EmailReminder] = Field(
        default_factory=lambda: [
            EmailReminder(days_before=1, time=datetime.time(9, 0, 0))
        ],
        sa_column=Column(EmailReminderListType, nullable=False),
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
    children_per_box: int | None = Field(default=None, ge=1)
    contact_name: str | None = Field(default=None, min_length=1, max_length=255)
    contact_phone: str | None = Field(default=None, min_length=1, max_length=100)
    f4k_wr_instagram: str | None = Field(default=None, min_length=1, max_length=255)
    f4k_wr_facebook: str | None = Field(default=None, min_length=1, max_length=255)
    f4k_wr_email: EmailStr | None = Field(default=None)
    f4k_wr_website: str | None = Field(default=None, min_length=1, max_length=255)
    f4k_wr_address: str | None = Field(default=None, min_length=1, max_length=255)
    email_reminders: list[EmailReminder] | None = Field(default=None)

    @field_validator("contact_phone")
    @classmethod
    def validate_contact_phone(cls, v: str | None) -> str | None:
        """Validate the contact phone number when configured."""
        if v is None:
            return None
        return validate_phone(v)

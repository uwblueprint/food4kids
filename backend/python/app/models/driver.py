from datetime import date
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from pydantic import EmailStr, computed_field, field_validator, model_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

from app.models.user import User
from app.utilities.utils import validate_phone

from .base import BaseModel

if TYPE_CHECKING:
    from .note_chain import NoteChain


class DriverBase(SQLModel):
    # No max_length: pydantic would check it against the raw submitted string,
    # before validate_phone normalizes. The real cap is on the normalized value
    # (MAX_STORED_PHONE_LENGTH, matching the varchar(32) column).
    phone: str | None = Field(default=None)
    partner_driver_name: str | None = Field(default=None, max_length=255)
    # Five slots, Monday = 0 through Friday = 4.
    availability: list[bool] = Field(
        default_factory=lambda: [False] * 5,
        sa_column=Column(JSON, nullable=False),
    )
    license_plate: str | None = Field(default=None, max_length=20)
    car_make_model: str | None = Field(default=None, max_length=255)
    active: bool = Field(default=True)
    address: str | None = Field(default=None, max_length=255)
    # One-to-one link to a threaded note chain, enforced unique at the DB level.
    # Created admin-only (read AND write) so drivers can't see or edit notes
    # written about them — see DriverService.create_driver. Set by the service,
    # not the client. This replaced the old flat `notes` string.
    note_chain_id: UUID | None = Field(
        default=None,
        foreign_key="note_chains.note_chain_id",
        nullable=True,
        ondelete="SET NULL",
        unique=True,
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """Validate phone number using phonenumbers library"""
        return validate_phone(v) if v else None

    @field_validator("availability")
    @classmethod
    def validate_availability(cls, v: list[bool]) -> list[bool]:
        if len(v) != 5:
            raise ValueError("availability must contain 5 slots, Monday = 0")
        return v


class Driver(DriverBase, BaseModel, table=True):
    __tablename__ = "drivers"

    driver_id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(
        foreign_key="users.user_id", unique=True, nullable=False, ondelete="CASCADE"
    )
    user: User = Relationship()
    note_chain: "NoteChain" = Relationship()


class DriverCreate(DriverBase):
    user_id: UUID  # link to created User


class DriverRead(DriverBase):
    model_config = {"from_attributes": True}

    driver_id: UUID
    user_id: UUID

    # These are from the User
    auth_id: str | None
    first_name: str
    last_name: str
    email: EmailStr
    role: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @model_validator(mode="before")
    @classmethod
    def extract_user_fields(cls, data: Any) -> Any:
        if (
            not isinstance(data, dict)
            and hasattr(data, "user")
            and data.user is not None
        ):
            user = data.user
            return {
                "driver_id": data.driver_id,
                "user_id": data.user_id,
                "phone": data.phone,
                "partner_driver_name": data.partner_driver_name,
                "availability": data.availability,
                "license_plate": data.license_plate,
                "car_make_model": data.car_make_model,
                "active": data.active,
                "address": data.address,
                "note_chain_id": data.note_chain_id,
                "auth_id": user.auth_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "role": user.role,
            }
        return data


class DriverListRead(DriverRead):
    """Driver table row with aggregates computed by the list query."""

    current_year_km: float = 0
    last_year_km: float = 0
    last_delivery: date | None = None
    is_active: bool = False


class DriverUpdate(SQLModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=255)
    last_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None)
    partner_driver_name: str | None = Field(default=None, max_length=255)
    availability: list[bool] | None = Field(default=None)
    address: str | None = Field(default=None, max_length=255)
    license_plate: str | None = Field(default=None, max_length=20)
    car_make_model: str | None = Field(default=None, max_length=255)
    active: bool | None = Field(default=None)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """Normalize on update too — ``update_driver_by_id`` assigns straight
        onto the row, and SQLModel table instances don't re-run validators on
        assignment, so without this an edit writes the raw client string."""
        if v is None:
            return None
        return validate_phone(v)

    @field_validator("availability")
    @classmethod
    def validate_availability(cls, v: list[bool] | None) -> list[bool] | None:
        if v is not None and len(v) != 5:
            raise ValueError("availability must contain 5 slots, Monday = 0")
        return v

    @field_validator(
        "first_name",
        "last_name",
        "availability",
        "active",
        mode="before",
    )
    @classmethod
    def reject_explicit_null(cls, v: Any) -> Any:
        """
        Reject an explicit ``null`` for fields whose columns are non-nullable
        (every field except ``partner_driver_name``, where null means "clear").

        The ``None`` default only means "not provided" — validators don't run
        for defaults, so reaching here with ``None`` means the client sent a
        null. Failing here yields a 422 instead of a NOT NULL violation at
        commit time.
        """
        if v is None:
            raise ValueError("cannot be null; omit the field to leave it unchanged")
        return v


class DriverRegister(SQLModel):
    """Driver registration request"""

    # User fields
    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(max_length=254)

    # Driver fields
    phone: str | None = Field(default=None)
    partner_driver_name: str | None = Field(default=None, max_length=255)
    availability: list[bool] = Field(default_factory=lambda: [False] * 5)
    license_plate: str | None = Field(default=None, max_length=20)
    car_make_model: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, max_length=255)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """Validate phone number using phonenumbers library"""
        return validate_phone(v) if v else None

    @field_validator("availability")
    @classmethod
    def validate_availability(cls, v: list[bool]) -> list[bool]:
        if len(v) != 5:
            raise ValueError("availability must contain 5 slots, Monday = 0")
        return v

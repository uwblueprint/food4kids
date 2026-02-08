from typing import Any
from uuid import UUID, uuid4

from pydantic import EmailStr, field_validator, model_validator
from sqlmodel import Field, Relationship, SQLModel

from app.models.user import User
from app.utilities.utils import validate_phone

from .base import BaseModel


class DriverBase(SQLModel):
    phone: str = Field(min_length=1, max_length=20)
    license_plate: str = Field(min_length=1, max_length=20)
    car_make_model: str = Field(min_length=1, max_length=255)
    active: bool = Field(default=True)
    notes: str = Field(default="", max_length=1024)
    address: str = Field(min_length=1, max_length=255)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number using phonenumbers library"""
        return validate_phone(v)


class Driver(DriverBase, BaseModel, table=True):
    __tablename__ = "drivers"

    driver_id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="users.user_id", unique=True, nullable=False, ondelete="CASCADE")
    user: User = Relationship()


class DriverCreate(DriverBase):
    user_id: UUID  # link to created User


class DriverRead(DriverBase):
    model_config = {"from_attributes": True}

    driver_id: UUID
    user_id: UUID

    # These are from the User
    auth_id: str
    name: str
    email: EmailStr
    role: str

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
                "license_plate": data.license_plate,
                "car_make_model": data.car_make_model,
                "active": data.active,
                "notes": data.notes,
                "address": data.address,
                "auth_id": user.auth_id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
            }
        return data


class DriverUpdate(SQLModel):
    phone: str | None = Field(default=None, min_length=1, max_length=20)
    address: str | None = Field(default=None, min_length=1, max_length=255)
    license_plate: str | None = Field(default=None, min_length=1, max_length=20)
    car_make_model: str | None = Field(default=None, min_length=1, max_length=255)
    active: bool | None = Field(default=None)
    notes: str | None = Field(default=None, max_length=1024)


class DriverUpdatePayload(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, min_length=1, max_length=20)
    address: str | None = Field(default=None, min_length=1, max_length=255)
    license_plate: str | None = Field(default=None, min_length=1, max_length=20)
    car_make_model: str | None = Field(default=None, min_length=1, max_length=255)
    active: bool | None = Field(default=None)
    notes: str | None = Field(default=None, max_length=1024)


class DriverRegister(SQLModel):
    """Driver registration request"""

    # User fields
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=8, max_length=100)

    # Driver fields
    phone: str = Field(min_length=1, max_length=20)
    license_plate: str = Field(min_length=1, max_length=20)
    car_make_model: str = Field(min_length=1, max_length=255)
    address: str = Field(min_length=1, max_length=255)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number using phonenumbers library"""
        return validate_phone(v)

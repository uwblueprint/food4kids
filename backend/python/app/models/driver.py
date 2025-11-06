from uuid import UUID, uuid4

from pydantic import EmailStr, field_validator
from sqlmodel import Field, SQLModel

# from app.utilities.utils import validate_phone

from .base import BaseModel


class DriverBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(unique=True, index=True, max_length=254)
    phone: str = Field(min_length=1, max_length=20)
    address: str = Field(min_length=1, max_length=255)
    license_plate: str = Field(min_length=1, max_length=20)
    car_make_model: str = Field(min_length=1, max_length=255)
    active: bool = Field(default=True)
    notes: str = Field(default="", max_length=1024)

    # @field_validator("phone")
    # @classmethod
    # def validate_phone(cls, v: str) -> str:
    #     """Validate phone number using phonenumbers library"""
    #     return validate_phone(v)


class Driver(DriverBase, BaseModel, table=True):
    __tablename__ = "drivers"

    driver_id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    auth_id: str = Field(nullable=False, unique=True, index=True)


class DriverCreate(DriverBase):
    password: str = Field(min_length=8, max_length=100)


class DriverRead(DriverBase):
    driver_id: UUID
    auth_id: str


class DriverUpdate(SQLModel):
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

    name: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(max_length=254)
    phone: str = Field(min_length=1, max_length=20)
    address: str = Field(min_length=1, max_length=255)
    license_plate: str = Field(min_length=1, max_length=20)
    car_make_model: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=100)

    # @field_validator("phone")
    # @classmethod
    # def validate_phone(cls, v: str) -> str:
    #     """Validate phone number using phonenumbers library"""
    #     return validate_phone(v)

from uuid import UUID, uuid4

from pydantic import EmailStr, field_validator
from sqlmodel import Field, SQLModel, Relationship

from app.utilities.utils import validate_phone

from .base import BaseModel

from app.models.user import User


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
    user_id: UUID = Field(foreign_key="users.user_id", unique=True, nullable=False)
    user: User = Relationship()


class DriverCreate(DriverBase):
    user_id: UUID  # link to created User


class DriverRead(DriverBase):
    driver_id: UUID
    auth_id: str
    user_id: UUID
    name: str
    email: EmailStr
    role: str  # comes from User


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

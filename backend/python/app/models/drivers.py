from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel


class DriverBase(SQLModel):

    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=1, max_length=20)
    address: str = Field(min_length=1, max_length=255)
    license_plate: str = Field(min_length=1, max_length=20)
    car_make_model: str = Field(min_length=1, max_length=255)
    active: bool = Field(default=True)
    notes: str = Field(default="", max_length=1024)

class Driver(DriverBase, table=True):
    __tablename__ = "drivers"

    driver_id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)

class DriverCreate(DriverBase):
    pass

class DriverRead(DriverBase):
    driver_id: UUID

class DriverUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=1, max_length=20)
    address: str | None = Field(default=None, min_length=1, max_length=255)
    license_plate: str | None = Field(default=None, min_length=1, max_length=20)
    car_make_model: str | None = Field(default=None, min_length=1, max_length=255)
    active: bool | None = Field(default=None)
    notes: str | None = Field(default=None, max_length=1024)
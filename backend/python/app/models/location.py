from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from .base import BaseModel


class LocationBase(SQLModel):
    """Shared fields between table and API models"""

    location_group_id: UUID | None = Field(
        foreign_key="location_groups.location_group_id", nullable=True
    )
    is_school: bool
    school_name: str | None = None
    contact_name: str
    address: str
    phone_number: str
    longitude: float
    latitude: float
    halal: bool
    dietary_restrictions: str | None = None
    num_children: int | None = None
    num_boxes: int
    notes: str | None = None


class Location(LocationBase, BaseModel, table=True):
    """Database table model"""

    __tablename__ = "locations"

    location_id: UUID = Field(default_factory=uuid4, primary_key=True)


class LocationCreate(LocationBase):
    """Create request model"""

    pass


class LocationRead(LocationBase):
    """Read response model"""

    location_id: UUID


class LocationUpdate(SQLModel):
    """Update request model"""

    location_id: UUID
    location_group_id: UUID | None = Field(
        foreign_key="location_groups.location_group_id", nullable=True
    )
    is_school: bool
    school_name: str | None = None
    contact_name: str
    address: str
    phone_number: str
    longitude: float
    latitude: float
    halal: bool
    dietary_restrictions: str | None = None
    num_children: int | None = None
    num_boxes: int
    notes: str | None = None

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .location_group import LocationGroup


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
    notes: str = Field(default="")


class Location(LocationBase, BaseModel, table=True):
    """Database table model"""

    __tablename__ = "locations"

    location_id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Relationship back to location group
    location_group: "LocationGroup" = Relationship(back_populates="locations")


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

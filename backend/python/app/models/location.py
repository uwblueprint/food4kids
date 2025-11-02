from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .location_group import LocationGroup


class LocationBase(SQLModel):
    """Shared fields between table and API models"""

    location_group_id: UUID | None = Field(
        default=None, foreign_key="location_groups.location_group_id", nullable=True
    )
    school_name: str | None = None
    contact_name: str
    address: str
    phone_number: str
    longitude: float | None = None
    latitude: float | None = None
    halal: bool
    dietary_restrictions: str = Field(default="")
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
    """Update request model with all fields optional"""

    location_group_id: UUID | None = None
    school_name: str | None = None
    contact_name: str | None = None
    address: str | None = None
    phone_number: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    halal: bool | None = None
    dietary_restrictions: str | None = None
    num_children: int | None = None
    num_boxes: int | None = None
    notes: str | None = None


class LocationImportError(SQLModel):
    address: str
    error: str


class LocationImportResponse(SQLModel):
    total_entries: int
    successful_entries: int
    failed_entries: int
    successful_locations: list[LocationRead]
    failed_locations: list[LocationImportError]

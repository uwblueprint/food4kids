from enum import Enum
from typing import TYPE_CHECKING, Protocol
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel, String

from .base import BaseModel

if TYPE_CHECKING:
    from .location_group import LocationGroup


class LocationState(str, Enum):
    """State of a location"""

    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


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
    place_id: str | None = None
    num_children: int | None = None
    num_boxes: int
    notes: str = Field(default="")
    state: LocationState = Field(default=LocationState.ACTIVE, sa_type=String)


class Location(LocationBase, BaseModel, table=True):
    """Database table model"""

    __tablename__ = "locations"

    location_id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Relationship back to location group
    location_group: "LocationGroup" = Relationship(back_populates="locations")


class LocationImportStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"


class LocationRowStatus(str, Enum):
    """Status for each row in a location import."""

    OK = "OK"
    MISSING_FIELDS = "MISSING_FIELDS"
    DUPLICATE = "DUPLICATE"
    INVALID_FORMAT = "INVALID_FORMAT"


class LocationImportEntry(SQLModel):
    """Parsed row from import file; all fields optional until validated."""

    contact_name: str | None = None
    address: str | None = None
    delivery_group: str | None = None
    phone_number: str | None = None
    num_boxes: int | None = None
    halal: bool | None = None
    dietary_restrictions: str | None = None


class ValidatedLocationImportEntry(Protocol):
    """Type view of LocationImportEntry after required-fields check. Use with TypeGuard."""

    contact_name: str
    address: str
    delivery_group: str
    phone_number: str
    num_boxes: int
    halal: bool | None
    dietary_restrictions: str | None


class LocationImportRow(SQLModel):
    row: int
    location: LocationImportEntry
    status: LocationRowStatus


class LocationImportResponse(SQLModel):
    status: LocationImportStatus
    total_rows: int
    successful_rows: int
    unsuccessful_rows: int
    rows: list[LocationImportRow]


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
    place_id: str | None = None
    num_children: int | None = None
    num_boxes: int | None = None
    notes: str | None = None

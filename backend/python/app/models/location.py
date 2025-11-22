from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .location_group import LocationGroup


class LocationState(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class LocationEntryStatus(str, Enum):
    OK = "OK"
    MISSING_FIELD = "Missing Field"
    DUPLICATE_ENTRY = "Local Duplicate Entry"
    UNKNOWN_ERROR = "Unknown Error"


class LocationMatchStatus(str, Enum):
    SIMILAR_MATCH = "Similar Match"
    DUPLICATE_MATCH = "Duplicate Match"
    NET_NEW = "Net New"


class LocationBase(SQLModel):
    """Shared fields between table and API models"""

    location_group_id: UUID | None = Field(
        default=None, foreign_key="location_groups.location_group_id", nullable=True
    )
    state: str = Field(default=LocationState.ACTIVE.value, max_length=20)
    school_name: str | None = None
    contact_name: str
    place_id: str | None = None
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
    state: str | None = None
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


class UploadedLocationBase(SQLModel):
    # TODO: eventually refactor
    """Required fields for uploaded location data"""
    contact_name: str | None = None
    address: str | None = None
    phone_number: str | None = None
    num_boxes: int | None = None
    dietary_restrictions: str | None = None
    halal: bool | None = None
    delivery_group: str | None = None


class LocationEntry(SQLModel):
    """Entry result from location import/validation"""
    row: int
    location: UploadedLocationBase
    missing_fields: list[str]
    status: LocationEntryStatus


class LocationLinkPayload(SQLModel):
    entries: list[LocationEntry]


class LocationEntriesResponse(SQLModel):
    total_entries: int
    successful_entries: int
    failed_entries: int
    entries: list[LocationEntry]


class LocationLinkEntry(SQLModel):
    location: UploadedLocationBase
    status: LocationMatchStatus
    duplicate_location: LocationRead | None = None
    similar_location: LocationRead | None = None
    row: int


class LinkLocationsResponse(SQLModel):
    total_entries: int
    new_entries: int
    duplicate_entries: int
    similar_entries: int
    entries: list[LocationLinkEntry]

from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel, String

from .base import BaseModel

if TYPE_CHECKING:
    from .location_group import LocationGroup
    from .note_chain import NoteChain


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
    halal: bool = Field(default=False)
    dietary_restrictions: str = Field(default="")
    place_id: str | None = None
    num_children: int | None = None
    num_boxes: int = Field(default=0)
    state: LocationState = Field(default=LocationState.ACTIVE, sa_type=String)
    notes: str = Field(default="")
    note_chain_id: UUID | None = Field(
        default=None, foreign_key="note_chains.note_chain_id", nullable=True
    )


class Location(LocationBase, BaseModel, table=True):
    """Database table model"""

    __tablename__ = "locations"

    location_id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Relationship back to location group
    location_group: "LocationGroup" = Relationship(back_populates="locations")
    note_chain: "NoteChain" = Relationship()


class LocationImportStatus(str, Enum):
    """Status of the import"""

    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


class AlertType(str, Enum):
    """Severity of an import alert — drives icon/colour on the frontend."""

    WARNING = "WARNING"
    ERROR = "ERROR"


class AlertCode(str, Enum):
    """Machine-readable reason code for an import alert."""

    # ERROR TYPES
    MISSING_FIELDS = "MISSING_FIELDS"
    INVALID_FORMAT = "INVALID_FORMAT"
    LOCAL_DUPLICATE = "LOCAL_DUPLICATE"

    # WARNING TYPES
    MISSING_DELIVERY_GROUP = "MISSING_DELIVERY_GROUP"
    PARTIAL_DUPLICATE = "PARTIAL_DUPLICATE"


class LocationImportAlert(SQLModel):
    """A single alert attached to an import row."""

    type: AlertType
    code: AlertCode
    message: str


class LocationImportEntry(SQLModel):
    """Parsed row from import file; all fields optional until validated."""

    contact_name: str | None = None
    address: str | None = None
    delivery_group: str | None = None
    phone_number: str | None = None
    num_boxes: int | None = None
    halal: bool | None = None
    dietary_restrictions: str | None = None


class ValidatedLocationImportEntry(LocationImportEntry):
    """LocationImportEntry with required fields guaranteed non-None after validation."""

    contact_name: str
    address: str
    phone_number: str
    delivery_group: str | None = None
    num_boxes: int | None = None
    halal: bool | None = None
    dietary_restrictions: str | None = None


class LocationImportRow(SQLModel):
    row: int
    location: LocationImportEntry
    alerts: list[LocationImportAlert]


class LocationImportResponse(SQLModel):
    status: LocationImportStatus
    total_rows: int
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
    note_chain_id: UUID | None = None

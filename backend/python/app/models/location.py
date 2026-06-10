from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel, String

from .base import BaseModel
from .enum import DeliveryTypeEnum

if TYPE_CHECKING:
    from .location_group import LocationGroup
    from .note_chain import NoteChain


class LocationState(str, Enum):
    """State of a location"""

    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class LocationBase(SQLModel):
    """Shared fields between table and API models"""

    location_group_id: UUID = Field(
        foreign_key="location_groups.location_group_id", nullable=False
    )
    name: str
    contact_name: str
    delivery_type: DeliveryTypeEnum = Field(sa_type=String)
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

    @property
    def location_group_name(self) -> str:
        """Name of the location's (required) delivery group.

        Surfaced on LocationRead so list views can show the group name without
        a second lookup. Requires location_group to be eager-loaded (see the
        selectinload calls in LocationService) to avoid an async lazy load.
        """
        return self.location_group.name


class AlertCode(str, Enum):
    """Machine-readable reason code for an import alert."""

    MISSING_FIELDS = "MISSING_FIELDS"
    INVALID_FORMAT = "INVALID_FORMAT"
    LOCAL_DUPLICATE = "LOCAL_DUPLICATE"
    MISSING_DELIVERY_GROUP = "MISSING_DELIVERY_GROUP"
    PARTIAL_DUPLICATE = "PARTIAL_DUPLICATE"


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
    # Required: every location must belong to a delivery group (the import
    # flags MISSING_DELIVERY_GROUP, and location_group_id is non-nullable).
    delivery_group: str
    num_boxes: int | None = None
    halal: bool | None = None
    dietary_restrictions: str | None = None


class LocationImportRow(SQLModel):
    row: int
    location: LocationImportEntry
    alerts: list[AlertCode]


class NetNewEntry(SQLModel):
    """A row in the import that has no matching existing location."""

    row: int
    contact_name: str
    address: str
    delivery_group: str | None = None
    phone_number: str
    num_boxes: int | None = None


class StaleEntry(SQLModel):
    """An existing location not present in the import; would be archived on ingest."""

    location_id: UUID
    contact_name: str
    address: str
    delivery_group: str | None = None
    phone_number: str


class ChangedFieldStr(SQLModel):
    new_value: str
    old_value: str


class ChangedFieldOptStr(SQLModel):
    new_value: str | None
    old_value: str | None


class ChangedFieldOptInt(SQLModel):
    new_value: int | None
    old_value: int | None


class ChangedEntry(SQLModel):
    """An existing location whose fields differ from the import row.

    Each field is either the plain new value (unchanged) or a ChangedField object
    carrying both new and old values.
    """

    contact_name: str
    address: str | ChangedFieldStr
    delivery_group: str | None | ChangedFieldOptStr = None
    phone_number: str | ChangedFieldStr
    num_children: int | None | ChangedFieldOptInt = None


class LocationImportResponse(SQLModel):
    """Combined validate + review-changes payload.

    success=False when any row has alerts. net_new/stale/changed describe how the
    import would affect the existing locations table; these are placeholders until
    the matching logic is implemented.
    """

    success: bool
    total_rows: int
    rows: list[LocationImportRow]
    net_new: list[NetNewEntry] = []
    stale: list[StaleEntry] = []
    changed: list[ChangedEntry] = []


class LocationCreate(LocationBase):
    """Create request model"""

    pass


class LocationRead(LocationBase):
    """Read response model"""

    location_id: UUID
    location_group_name: str


class LocationUpdate(SQLModel):
    """Update request model with all fields optional"""

    location_group_id: UUID | None = None
    name: str | None = None
    contact_name: str | None = None
    delivery_type: DeliveryTypeEnum | None = None
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


class LocationIngestRequest(SQLModel):
    net_new: list[ValidatedLocationImportEntry]
    stale: list[LocationRead]


class LocationIngestResponse(SQLModel):
    created: list[LocationRead]
    archived: list[LocationRead]

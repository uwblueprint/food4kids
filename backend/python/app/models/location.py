from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import computed_field
from sqlmodel import Field, Relationship, SQLModel, String

from .base import BaseModel
from .enum import DeliveryTypeEnum, LocationStatusEnum

if TYPE_CHECKING:
    from .location_group import LocationGroup
    from .note_chain import NoteChain


class LocationBase(SQLModel):
    """Shared fields between table and API models"""

    location_group_id: UUID = Field(
        foreign_key="location_groups.location_group_id", nullable=False
    )
    name: str
    contact_name: str
    address: str
    phone_primary: str
    phone_secondary: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    halal: bool = Field(default=False)
    dietary_restrictions: str = Field(default="")
    place_id: str | None = None
    # Number of children served at this location. Required: the box count is
    # derived from this (ceil(num_children / children_per_box)); there is no
    # stored num_boxes. See app.utilities.boxes.compute_boxes.
    num_children: int = Field(default=0, ge=0)
    # Kind of recipient (School/Family). Required — no default — per main's
    # rename/persist migration; enforced uniform within a RouteGroup at
    # generation time.
    delivery_type: DeliveryTypeEnum = Field(sa_type=String)
    # Stored bit: was this location in the most recent relevant spreadsheet
    # upload? The user-facing three-state status (Active/Unscheduled/Inactive)
    # is derived from this plus whether the location appears in a present/
    # future route — see LocationRead.status.
    in_roster: bool = Field(default=True)
    notes: str = Field(default="")
    note_chain_id: UUID | None = Field(
        default=None,
        foreign_key="note_chains.note_chain_id",
        nullable=True,
        ondelete="SET NULL",
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
    phone_primary: str | None = None
    phone_secondary: str | None = None
    num_children: int | None = None
    halal: bool | None = None
    dietary_restrictions: str | None = None


class ValidatedLocationImportEntry(LocationImportEntry):
    """LocationImportEntry with required fields guaranteed non-None after validation."""

    contact_name: str
    address: str
    phone_primary: str
    phone_secondary: str | None = None
    # Required: every location must belong to a delivery group (the import
    # flags MISSING_DELIVERY_GROUP, and location_group_id is non-nullable).
    delivery_group: str
    num_children: int | None = None
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
    phone_primary: str
    phone_secondary: str | None = None
    num_children: int | None = None


class StaleEntry(SQLModel):
    """An existing location not present in the import; would be set
    in_roster=False on ingest."""

    location_id: UUID
    contact_name: str
    address: str
    delivery_group: str | None = None
    phone_primary: str
    phone_secondary: str | None = None


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
    phone_primary: str | ChangedFieldStr
    phone_secondary: str | None | ChangedFieldOptStr = None
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
    """Read response model.

    `has_future_route` is populated by the service layer (one batched query
    against route_stops + route_groups), and `status` is derived from it +
    in_roster. See LocationStatusEnum for the precedence rule.
    """

    location_id: UUID
    location_group_name: str
    # Populated by the service; defaulted to False so single-row construction
    # without a service round-trip still works (will report UNSCHEDULED/INACTIVE).
    has_future_route: bool = False
    assigned_route: str | None = None
    last_delivery_date: datetime | None = None
    total_deliveries: int = 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def status(self) -> LocationStatusEnum:
        if self.has_future_route:
            return LocationStatusEnum.ACTIVE
        if self.in_roster:
            return LocationStatusEnum.UNSCHEDULED
        return LocationStatusEnum.INACTIVE


class LocationUpdate(SQLModel):
    """Update request model with all fields optional"""

    location_group_id: UUID | None = None
    name: str | None = None
    contact_name: str | None = None
    address: str | None = None
    phone_primary: str | None = None
    phone_secondary: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    halal: bool | None = None
    dietary_restrictions: str | None = None
    place_id: str | None = None
    num_children: int | None = None
    delivery_type: DeliveryTypeEnum | None = None
    in_roster: bool | None = None
    notes: str | None = None
    note_chain_id: UUID | None = None


class LocationIngestRequest(SQLModel):
    """Ingest request — `delivery_type` applies to every net-new row in this
    import (one Apricot sheet = one delivery type)."""

    delivery_type: DeliveryTypeEnum
    net_new: list[ValidatedLocationImportEntry]
    stale: list[LocationRead]


class LocationIngestResponse(SQLModel):
    created: list[LocationRead]
    archived: list[LocationRead]

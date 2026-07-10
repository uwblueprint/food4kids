from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .location import Location
    from .route import Route
    from .route_stop_snapshot import RouteStopSnapshot


class RouteStopBase(SQLModel):
    """Shared fields between table and API models"""

    route_id: UUID = Field(foreign_key="routes.route_id")
    location_id: UUID = Field(foreign_key="locations.location_id")
    stop_number: int = Field(ge=1)  # Stop number in the route sequence


class RouteStop(RouteStopBase, BaseModel, table=True):
    """Database table model for Route Stops"""

    __tablename__ = "route_stops"
    __table_args__ = (
        # Stop ordering within a route must be unambiguous.
        UniqueConstraint(
            "route_id", "stop_number", name="uq_route_stops_route_id_stop_number"
        ),
        # A location appears at most once per route — structural guard against
        # double-delivering to the same family within one route. (Duplicates
        # across routes in the same RouteGroup still need an app-level check.)
        UniqueConstraint(
            "route_id", "location_id", name="uq_route_stops_route_id_location_id"
        ),
    )

    route_stop_id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)

    # Relationships
    route: "Route" = Relationship(back_populates="route_stops")
    # Live FK to Location: while a route is upcoming, reads pull from here;
    # once snapshotted on completion, reads should COALESCE the snapshot's
    # fields over the live location's.
    location: "Location" = Relationship()
    # 1:1 with RouteStopSnapshot — presence implies the parent route is frozen.
    # See route.py for why we use Optional[X] (not "X | None") here.
    snapshot: Optional["RouteStopSnapshot"] = Relationship(
        back_populates="route_stop",
        sa_relationship_kwargs={
            "uselist": False,
            "cascade": "all, delete-orphan",
        },
    )


class RouteStopCreate(RouteStopBase):
    """Create request model"""

    pass


class RouteStopRead(RouteStopBase):
    """Read response model"""

    route_stop_id: UUID


class RouteStopUpdate(SQLModel):
    """Update request model - all optional"""

    route_id: UUID | None = None
    location_id: UUID | None = None
    stop_number: int | None = None


class RouteStopDetailRead(SQLModel):
    """A single ordered stop on a route, assembled with snapshot-over-live
    field precedence: for a frozen (past) route the route_stop_snapshot wins,
    otherwise the live Location is read. Embedded in RouteDetailRead.

    Notes are intentionally NOT embedded: note_chain_id points at the stop's
    note chain, fetched separately via GET /note-chains/{id}/notes.
    """

    stop_number: int
    address: str
    contact_name: str
    phone_primary: str
    # Secondary phone lives only on the live Location (snapshots don't capture
    # it), so it's read from there regardless of frozen state.
    phone_secondary: str | None = None
    boxes: int
    note_chain_id: UUID | None = None

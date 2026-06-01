from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

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

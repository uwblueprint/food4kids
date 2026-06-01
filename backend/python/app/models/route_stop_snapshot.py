from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .route_stop import RouteStop


class RouteStopSnapshotBase(SQLModel):
    """Frozen per-stop delivery data captured when a route is completed.

    Locations mutate in place (moves = update the Location row); without this
    snapshot, looking at a past route would show the location's current data
    rather than what was actually delivered to. Reads should COALESCE the
    snapshot fields with the live Location fields — present = use snapshot.
    """

    address: str = Field(min_length=1)
    contact_name: str = Field(min_length=1)
    phone_number: str = Field(min_length=1)
    num_boxes: int = Field(ge=0)
    notes: str = Field(default="")
    latitude: float
    longitude: float


class RouteStopSnapshot(RouteStopSnapshotBase, BaseModel, table=True):
    """Database table model. One row per RouteStop; existence implies frozen."""

    __tablename__ = "route_stop_snapshots"

    route_stop_id: UUID = Field(
        foreign_key="route_stops.route_stop_id",
        primary_key=True,
        nullable=False,
        ondelete="CASCADE",
    )

    route_stop: "RouteStop" = Relationship(back_populates="snapshot")


class RouteStopSnapshotRead(RouteStopSnapshotBase):
    """Read response model"""

    route_stop_id: UUID

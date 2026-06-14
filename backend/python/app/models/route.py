from datetime import datetime, time
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Text
from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .driver import Driver
    from .note_chain import NoteChain
    from .route_group import RouteGroup
    from .route_snapshot import RouteSnapshot
    from .route_stop import RouteStop


class RouteBase(SQLModel):
    """Shared fields between table and API models"""

    name: str = Field(default="", min_length=1, max_length=255)
    notes: str = Field(default="", max_length=1000)
    length: float = Field(ge=0.0)  # in km, must be non-negative
    # Explicit TEXT (not VARCHAR) so we can't hit a hard failure on long
    # routes.
    encoded_polyline: str | None = Field(default=None, sa_type=Text)
    polyline_updated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    ends_at_warehouse: bool = Field(default=False)
    # Per-driver start time for this route (driver start times are staggered).
    # Nullable: unset until scheduled.
    start_time: time | None = Field(default=None)
    # Each Route belongs to exactly one RouteGroup (one drive_date).
    route_group_id: UUID = Field(
        foreign_key="route_groups.route_group_id",
        nullable=False,
        ondelete="CASCADE",
        index=True,
    )
    # Nullable: a route is "unassigned" iff driver_id IS NULL. Driver deletion
    # nullifies rather than cascades (driver leaving shouldn't delete routes).
    driver_id: UUID | None = Field(
        default=None,
        foreign_key="drivers.driver_id",
        nullable=True,
        ondelete="SET NULL",
        index=True,
    )
    # Lineage pointer: set by Duplicate Route Group (when that ships) so a
    # bulk-edit-forward operation can walk the chain. Nullable; freshly
    # generated routes have no parent. SET NULL on parent delete — lineage is
    # informational, not load-bearing.
    cloned_from_route_id: UUID | None = Field(
        default=None,
        foreign_key="routes.route_id",
        nullable=True,
        ondelete="SET NULL",
        index=True,
    )
    note_chain_id: UUID | None = Field(
        default=None,
        foreign_key="note_chains.note_chain_id",
        nullable=True,
        ondelete="SET NULL",
    )


class Route(RouteBase, BaseModel, table=True):
    """Database table model for Routes"""

    __tablename__ = "routes"

    route_id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)

    # Relationships
    route_stops: list["RouteStop"] = Relationship(
        back_populates="route", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    route_group: "RouteGroup" = Relationship(back_populates="routes")
    # Optional[] (not "X | None") because SQLAlchemy's relationship resolver
    # parses string annotations as class names — the | None union syntax fails
    # to load. Optional["X"] works because Optional is imported at module
    # level and SQLAlchemy unwraps it correctly.
    driver: Optional["Driver"] = Relationship()
    # 1:1 with RouteSnapshot — presence implies the route is frozen.
    snapshot: Optional["RouteSnapshot"] = Relationship(
        back_populates="route",
        sa_relationship_kwargs={
            "uselist": False,
            "cascade": "all, delete-orphan",
        },
    )
    note_chain: "NoteChain" = Relationship()


class RouteCreate(RouteBase):
    """Create request model"""

    pass


class RouteRead(RouteBase):
    """Read response model"""

    route_id: UUID


class RouteUpdate(SQLModel):
    """Update request model - all optional.

    Edits are permitted on completed routes too: the snapshot is the *default*
    historical record, but admins can correct it. UI should frame edits on
    frozen routes as 'correct the record' rather than 'change the plan'.
    """

    name: str | None = None
    notes: str | None = None
    length: float | None = None
    encoded_polyline: str | None = None
    polyline_updated_at: datetime | None = None
    ends_at_warehouse: bool | None = None
    start_time: time | None = None
    driver_id: UUID | None = None
    note_chain_id: UUID | None = None


class RouteWithDateRead(SQLModel):
    """Read response model for routes with drive date information.

    drive_date is sourced from RouteGroup.drive_date via the route_group
    relationship.
    """

    route_id: UUID
    name: str
    notes: str
    length: float
    drive_date: datetime


class SuggestedDriverRead(SQLModel):
    """A driver suggested for a route, ranked by how many of the route's
    locations they've delivered to on past (completed) routes."""

    driver_id: UUID
    name: str
    score: int


class RoutePatchRequest(SQLModel):
    """Request body for PATCH /routes/{route_id}.

    All fields are optional - only provided fields will be updated.
    If location_ids is provided, the route stops will be fully replaced
    and the routing algorithm will be re-run to update polyline + mileage.
    """

    name: str | None = None
    notes: str | None = None
    driver_id: UUID | None = None
    start_time: time | None = None
    location_ids: list[UUID] | None = None  # new ordered list of location IDs

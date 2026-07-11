from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .route import Route


class RouteSnapshotBase(SQLModel):
    """Frozen route-level data captured when a route is completed.

    Holds the warehouse start coordinates (which can drift —
    SystemSettings.warehouse_* are mutable) and the credited route length.
    The presence of a RouteSnapshot row is the canonical "this route is
    frozen" signal — there is no separate flag column on Route.
    """

    start_address: str = Field(min_length=1)
    start_latitude: float
    start_longitude: float
    # Route.length as credited at freeze time (and updated by frozen-route
    # amendments). Reconciliation hooks diff against THIS, never the mutable
    # live Route.length — the ledger must move exactly what was credited.
    length_km: float = Field(ge=0.0)


class RouteSnapshot(RouteSnapshotBase, BaseModel, table=True):
    """Database table model. One row per Route; existence implies frozen."""

    __tablename__ = "route_snapshots"

    route_id: UUID = Field(
        foreign_key="routes.route_id",
        primary_key=True,
        nullable=False,
        ondelete="CASCADE",
    )

    route: "Route" = Relationship(back_populates="snapshot")


class RouteSnapshotRead(RouteSnapshotBase):
    """Read response model"""

    route_id: UUID

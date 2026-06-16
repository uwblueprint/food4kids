from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .route import Route


class RouteGroupBase(SQLModel):
    """Shared fields between table and API models"""

    name: str = Field(min_length=1, max_length=255, nullable=False)
    notes: str = Field(default="")
    drive_date: datetime


class RouteGroup(RouteGroupBase, BaseModel, table=True):
    """Database table model for Route Groups.

    A RouteGroup is one day's batch of routes (one generation run). Routes
    belong to exactly one RouteGroup via Route.route_group_id.
    """

    __tablename__ = "route_groups"

    route_group_id: UUID = Field(
        default_factory=uuid4, primary_key=True, nullable=False
    )

    # Direct one-to-many relationship to the routes in this group. Cascade
    # delete: dropping a group drops its routes (and via their cascades, their
    # stops + snapshots).
    routes: list["Route"] = Relationship(
        back_populates="route_group",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    @property
    def num_routes(self) -> int:
        """Computed property for number of routes in this group"""
        return len(self.routes)


class RouteGroupCreate(RouteGroupBase):
    """Create request model"""

    pass


class RouteReadSummary(SQLModel):
    """Lightweight route info returned inside a route group response"""

    route_id: UUID
    name: str
    notes: str = ""
    length: float = 0


class RouteGroupRead(RouteGroupBase):
    """Read response model"""

    route_group_id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    num_routes: int
    num_locations: int = 0
    num_boxes: int = 0
    num_drivers_assigned: int = 0
    delivery_type: str | None = None
    status: str = "Archived"
    routes: list[RouteReadSummary] = []


class RouteGroupUpdate(SQLModel):
    """Update request model - all optional"""

    name: str | None = None
    notes: str | None = None
    drive_date: datetime | None = None

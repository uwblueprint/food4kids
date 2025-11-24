from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .route_group_membership import RouteGroupMembership
    from .route_stop import RouteStop

class RouteBase(SQLModel):
    """Shared fields between table and API models"""

    name: str = Field(default="", min_length=1, max_length=255)  # can change this later
    notes: str = Field(default="", max_length=1000)  # can change this later
    length: float = Field(ge=0.0)  # in km, must be non-negative
    encoded_polyline: str | None = Field(default=None, max_length=10000)
    expires_at: datetime | None = Field(default=None)
    last_refreshed: datetime | None = Field(default=None)


class Route(RouteBase, BaseModel, table=True):
    """Database table model for Routes

    Note: Routes are immutable once created
    """

    __tablename__ = "routes"

    route_id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)

    # Relationship to route stops
    route_stops: list["RouteStop"] = Relationship(
        back_populates="route", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    # Relationship to route group memberships
    route_group_memberships: list["RouteGroupMembership"] = Relationship(
        back_populates="route", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class RouteCreate(RouteBase):
    """Create request model"""

    pass


class RouteRead(RouteBase):
    """Read response model"""

    route_id: UUID


class RouteUpdate(SQLModel):
    """Update request model - all optional

    Note: Routes are meant to be immutable, but this allows updates if needed
    """

    name: str | None = None
    notes: str | None = None
    length: float | None = None
    encoded_polyline: str | None = None
    expires_at: datetime | None = None
    last_refreshed: datetime | None = None

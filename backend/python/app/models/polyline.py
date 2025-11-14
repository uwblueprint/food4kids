from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .routes import Route


class PolylineBase(SQLModel):
    """Shared fields between table and API models"""

    route_id: UUID = Field(foreign_key="routes.route_id")
    encoded_polyline: str = Field(min_length=1, max_length=10000)
    expires_at: datetime | None = Field(default=None)


class Polyline(PolylineBase, BaseModel, table=True):
    """Database table model for route polylines

    Stores compressed polyline data for routes with expiry tracking
    """

    __tablename__ = "polylines"

    polyline_id: UUID = Field(default=uuid4, primary_key=True, nullable=False)

    # Relationship back to route
    route: "Route" = Relationship(back_populates="polylines")


class PolylineCreate(PolylineBase):
    """Create request model"""

    pass


class PolylineRead(PolylineBase):
    """Read response model"""

    polyline_id: UUID


class PolylineUpdate(SQLModel):
    """Update request model - all optional"""

    route_id: UUID | None = None
    encoded_polyline: str | None = None
    expires_at: datetime | None = None

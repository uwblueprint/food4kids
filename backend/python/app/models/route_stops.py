from uuid import UUID, uuid4
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Field, SQLModel, Relationship

from .base import BaseModel

from .route import Route


class RouteStopBase(SQLModel):
    """Shared fields between table and API models"""

    route_id: UUID = Field(
        foreign_key="routes.route_id"
    )
    location_id: UUID = Field(
        foreign_key="locations.location_id"
    )
    stop_number: int = Field(ge=1)  # Stop number in the route sequence


class RouteStop(RouteStopBase, BaseModel, table=True):
    """Database table model for Route Stops"""

    __tablename__ = "route_stops"

    route_stop_id: UUID = Field(
        default=uuid4,
        primary_key=True,
        nullable=False
    )

    # Relationship back to route
    route: "Route" = Relationship(back_populates="route_stops")


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
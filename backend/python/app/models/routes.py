from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel, Relationship

from .base import BaseModel


class RouteBase(SQLModel):
    """Shared fields between table and API models"""
    name: str = Field(default="", min_length=1, max_length=255) # can change this later
    notes: str = Field(default="", max_length=1000) # can change this later
    length: float = Field(ge=0.0)  # in km, must be non-negative


class Route(RouteBase, BaseModel, table=True):
    """Database table model for Routes
    
    Note: Routes are immutable once created
    """

    __tablename__ = "routes"

    route_id: UUID = Field(
        default=uuid4,
        primary_key=True,
        nullable=False
    )

    # Relationship to route stops
    route_stops: list["RouteStop"] = Relationship(
        back_populates="route",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
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

    route_group_id: UUID | None = None
    name: str | None = None
    notes: str | None = None
    length: float | None = None
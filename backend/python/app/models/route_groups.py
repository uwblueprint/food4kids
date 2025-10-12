from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from .base import BaseModel


class RouteGroupBase(SQLModel):
    """Shared fields between table and API models"""

    name: str = Field(min_length=1, max_length=255)
    notes: str = Field(default="")
    num_routes: int = Field(default=0)
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RouteGroup(RouteGroupBase, table=True):
    """Database table model for Route Groups"""

    __tablename__ = "route_groups"

    route_group_id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)


class RouteGroupCreate(RouteGroupBase):
    """Create request model"""

    pass


class RouteGroupRead(RouteGroupBase):
    """Read response model"""

    route_group_id: UUID


class RouteGroupUpdate(SQLModel):
    """Update request model - all optional"""

    name: str | None = None
    notes: str | None = None
    num_routes: int | None = None
    date: datetime | None = None

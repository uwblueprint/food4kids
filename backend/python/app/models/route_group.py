from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from pydantic import validator
from sqlalchemy import Column, DateTime

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .route import Route
    from .route_group_membership import RouteGroupMembership


class RouteGroupBase(SQLModel):
    """Shared fields between table and API models"""

    name: str = Field(min_length=1, max_length=255, nullable=False)
    notes: str = Field(default="")
    drive_date: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )

    @validator("drive_date")
    def enforce_est(cls, v: datetime) -> datetime:
        est_tz = ZoneInfo("America/Toronto")
        if v.tzinfo is None:
            # Assumes naive datetimes (like from the seed script) are already EST
            return v.replace(tzinfo=est_tz)
        # Converts other timezone-aware datetimes to EST
        return v.astimezone(est_tz)
    


class RouteGroup(RouteGroupBase, BaseModel, table=True):
    """Database table model for Route Groups"""

    __tablename__ = "route_groups"

    route_group_id: UUID = Field(
        default_factory=uuid4, primary_key=True, nullable=False
    )

    # Relationship to route group memberships
    route_group_memberships: list["RouteGroupMembership"] = Relationship(
        back_populates="route_group",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    @property
    def routes(self) -> list["Route"]:
        """Computed property to get the actual Route objects in this group"""
        return [membership.route for membership in self.route_group_memberships]

    @property
    def num_routes(self) -> int:
        """Computed property for number of routes in this group"""
        return len(self.route_group_memberships)


class RouteGroupCreate(RouteGroupBase):
    """Create request model"""

    pass


class RouteGroupRead(RouteGroupBase):
    """Read response model"""

    route_group_id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    num_routes: int


class RouteGroupUpdate(SQLModel):
    """Update request model - all optional"""

    name: str | None = None
    notes: str | None = None
    drive_date: datetime | None = None

    @validator("drive_date")
    def enforce_est(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return v
        est_tz = ZoneInfo("America/Toronto")
        if v.tzinfo is None:
            # Assumes naive datetimes (like from the seed script) are already EST
            return v.replace(tzinfo=est_tz)
        # Converts other timezone-aware datetimes to EST
        return v.astimezone(est_tz)

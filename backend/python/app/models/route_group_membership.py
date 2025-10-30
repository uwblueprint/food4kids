from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .route import Route
    from .route_group import RouteGroup


class RouteGroupMembershipBase(SQLModel):
    """Shared fields between table and API models"""

    route_group_id: UUID = Field(foreign_key="route_groups.route_group_id")
    route_id: UUID = Field(foreign_key="routes.route_id")


class RouteGroupMembership(RouteGroupMembershipBase, BaseModel, table=True):
    """Database table model for Route Group Memberships"""

    __tablename__ = "route_group_memberships"

    route_group_membership_id: UUID = Field(
        default_factory=uuid4, primary_key=True, nullable=False
    )

    # Relationships
    route_group: "RouteGroup" = Relationship(back_populates="route_group_memberships")
    route: "Route" = Relationship(back_populates="route_group_memberships")


class RouteGroupMembershipCreate(RouteGroupMembershipBase):
    """Create request model"""

    pass


class RouteGroupMembershipRead(RouteGroupMembershipBase):
    """Read response model"""

    route_group_membership_id: UUID


class RouteGroupMembershipUpdate(SQLModel):
    """Update request model - all optional"""

    route_group_id: UUID | None = None
    route_id: UUID | None = None

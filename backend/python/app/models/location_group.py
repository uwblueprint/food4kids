from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from .base import BaseModel


class LocationGroupBase(SQLModel):
    """Shared fields between table and API models"""

    name: str = Field(unique=True, index=True)
    color: str  # TODO: Decide if this is going to be an enum or a string
    notes: str | None = None


class LocationGroup(LocationGroupBase, BaseModel, table=True):
    """Location group model"""

    __tablename__ = "location_groups"
    location_group_id: UUID = Field(default_factory=uuid4, primary_key=True)
    num_locations: int = Field(default=0)


class LocationGroupCreate(LocationGroupBase):
    """Location group creation request"""

    location_ids: list[int] = Field(min_length=1)


class LocationGroupRead(LocationGroupBase):
    """Location group response model"""

    location_group_id: UUID
    num_locations: int


class LocationGroupUpdate(SQLModel):
    """Location group update request - all optional"""

    name: str | None = Field(default=None)
    color: str | None = Field(default=None)
    notes: str | None = Field(default=None)

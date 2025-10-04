from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel
from .base import BaseModel


class LocationGroupBase(SQLModel):
    """Shared fields between table and API models"""

    name: str = Field(unique=True, index=True)
    color: str  # TODO: Decide if this is going to be an enum or a string
    notes: Optional[str] = None


class LocationGroup(LocationGroupBase, BaseModel, table=True):
    """Location group model"""

    __tablename__ = "location_groups"
    location_group_id: UUID = Field(default_factory=uuid4, primary_key=True)


class LocationGroupCreate(LocationGroupBase):
    """Location group creation request"""

    pass


class LocationGroupRead(LocationGroupBase):
    """Location group response model"""

    location_group_id: UUID


class LocationGroupUpdate(SQLModel):
    """Location group update request - all optional"""

    name: Optional[str] = Field(default=None)
    color: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)

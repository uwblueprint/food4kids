from uuid import UUID, uuid4
from typing import Optional
from sqlmodel import SQLModel, Field
from .base import BaseModel


class LocationBase(SQLModel, table=True):
    """Shared fields between table and API models"""

    location_group_id: Optional[UUID] = Field(
        foreign_key="location_groups.location_group_id", nullable=True)
    is_school: bool
    school_name: Optional[str] = None
    contact_name: str
    address: str
    phone_number: str
    longitude: float
    latitude: float
    halal: bool
    dietary_restrictions: Optional[str] = None
    num_children: Optional[int] = None
    num_boxes: int
    notes: Optional[str] = None


class Location(LocationBase, BaseModel, table=True):
    """Database table model"""
    __tablename__ = "locations"

    location_id: UUID = Field(default_factory=uuid4, primary_key=True)


class LocationCreate(LocationBase):
    """Create request model"""
    pass


class LocationRead(LocationBase):
    """Read response model"""
    location_id: UUID


class LocationUpdate(SQLModel):
    """Update request model"""
    location_id: UUID
    location_group_id: Optional[UUID] = Field(
        foreign_key="location_groups.location_group_id", nullable=True)
    is_school: bool
    school_name: Optional[str] = None
    contact_name: str
    address: str
    phone_number: str
    longitude: float
    latitude: float
    halal: bool
    dietary_restrictions: Optional[str] = None
    num_children: Optional[int] = None
    num_boxes: int
    notes: Optional[str] = None

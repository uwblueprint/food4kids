from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from .base import BaseModel


class LocationMappingBase(SQLModel):
    """Shared fields between table and API models"""

    contact_name: str
    address: str
    location_delivery_group: str
    phone_number: str
    num_boxes: int
    dietary_restrictions: str = Field(default="")


class LocationMapping(LocationMappingBase, BaseModel, table=True):
    """Database table model"""

    __tablename__ = "location_mappings"

    location_mapping_id: UUID = Field(default_factory=uuid4, primary_key=True)


class LocationMappingCreate(LocationMappingBase):
    """Create request model"""

    pass


class LocationMappingRead(LocationMappingBase):
    """Read response model"""

    location_mapping_id: UUID


class LocationMappingUpdate(SQLModel):
    """Update request model with all fields optional"""

    contact_name: str | None = None
    address: str | None = None
    location_delivery_group: str | None = None
    phone_number: str | None = None
    num_boxes: int | None = None
    dietary_restrictions: str | None = None

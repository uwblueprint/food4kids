from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from .base import BaseModel

DEFAULT_MAPPING_NAME = "Location Mapping"


class RequiredLocationField(str, Enum):
    CONTACT_NAME = "contact_name"
    ADDRESS = "address"
    DELIVERY_GROUP = "delivery_group"
    PHONE_NUMBER = "phone_number"
    NUM_BOXES = "num_boxes"
    FOOD_RESTRICTIONS = "food_restrictions"


class LocationMappingBase(SQLModel):
    """Shared fields between table and API models"""

    mapping_name: str = Field(default=DEFAULT_MAPPING_NAME)
    mapping: dict[str, str] = Field(
        default_factory=dict, sa_column=Column(JSON))


class LocationMappingRead(LocationMappingBase):
    """Read response model for location mappings"""

    mapping_id: UUID


class LocationMappingCreate(LocationMappingBase):
    """Create request model for location mappings"""

    pass


class LocationMapping(LocationMappingBase, BaseModel, table=True):
    """Database table model for location mappings"""

    __tablename__ = "location_mappings"

    mapping_id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Define relationships to other tables if needed
    # admin_id: UUID = Field(foreign_key="admins.admin_id")
    # admin: "Admin" = Relationship(back_populates="location_mappings")


class LocationMappingPreview(SQLModel):
    """Location mappings preview from uploaded file"""

    preview_headers: list[str]

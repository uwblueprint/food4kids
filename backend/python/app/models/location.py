<<<<<<< HEAD
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .location_group import LocationGroup

=======
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from .base import BaseModel

>>>>>>> 60cc40f1582d3e202aafec387e2306bfd622a8a6

class LocationBase(SQLModel):
    """Shared fields between table and API models"""

    location_group_id: UUID | None = Field(
<<<<<<< HEAD
        default=None, foreign_key="location_groups.location_group_id", nullable=True
=======
        foreign_key="location_groups.location_group_id", nullable=True
>>>>>>> 60cc40f1582d3e202aafec387e2306bfd622a8a6
    )
    is_school: bool
    school_name: str | None = None
    contact_name: str
    address: str
    phone_number: str
    longitude: float
    latitude: float
    halal: bool
    dietary_restrictions: str | None = None
    num_children: int | None = None
    num_boxes: int
<<<<<<< HEAD
    notes: str = Field(default="")
=======
    notes: str | None = None
>>>>>>> 60cc40f1582d3e202aafec387e2306bfd622a8a6


class Location(LocationBase, BaseModel, table=True):
    """Database table model"""

    __tablename__ = "locations"

    location_id: UUID = Field(default_factory=uuid4, primary_key=True)

<<<<<<< HEAD
    # Relationship back to location group
    location_group: "LocationGroup" = Relationship(back_populates="locations")

=======
>>>>>>> 60cc40f1582d3e202aafec387e2306bfd622a8a6

class LocationCreate(LocationBase):
    """Create request model"""

    pass


class LocationRead(LocationBase):
    """Read response model"""

    location_id: UUID


class LocationUpdate(SQLModel):
    """Update request model"""

    location_id: UUID
    location_group_id: UUID | None = Field(
<<<<<<< HEAD
        default=None, foreign_key="location_groups.location_group_id", nullable=True
=======
        foreign_key="location_groups.location_group_id", nullable=True
>>>>>>> 60cc40f1582d3e202aafec387e2306bfd622a8a6
    )
    is_school: bool
    school_name: str | None = None
    contact_name: str
    address: str
    phone_number: str
    longitude: float
    latitude: float
    halal: bool
    dietary_restrictions: str | None = None
    num_children: int | None = None
    num_boxes: int
    notes: str | None = None

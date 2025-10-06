from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from .base import BaseModel


class DriverAssignmentBase(SQLModel):
    """Shared fields between table and API models"""

    driver_id: UUID = Field(foreign_key="drivers.driver_id")
    route_id: UUID = Field(foreign_key="routes.route_id")
    time: datetime = Field()
    completed: bool = Field(default=False)


class DriverAssignment(DriverAssignmentBase, BaseModel, table=True):
    """Database table model"""

    __tablename__ = "driver_assignments"

    driver_assignment_id: UUID = Field(default_factory=uuid4, primary_key=True)


class DriverAssignmentCreate(DriverAssignmentBase):
    """Create request model"""

    pass


class DriverAssignmentRead(DriverAssignmentBase):
    """Read response model"""

    driver_assignment_id: UUID


class DriverAssignmentUpdate(SQLModel):
    """Update request model - all optional"""

    time: datetime | None = Field(default=None)
    completed: bool | None = Field(default=None)

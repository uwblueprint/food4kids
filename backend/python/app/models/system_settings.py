import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from .base import BaseModel


class SystemSettingsBase(SQLModel):
    """Shared fields between table and API models"""

    default_cap: int | None = Field(default=None)
    route_start_time: datetime.time | None = Field(default=None)
    warehouse_location: str | None = Field(default=None, min_length=1)
    warehouse_longitude: float | None = None
    warehouse_latitude: float | None = None


class SystemSettings(SystemSettingsBase, BaseModel, table=True):
    """Database table model"""

    __tablename__ = "system_settings"

    system_settings_id: UUID = Field(default_factory=uuid4, primary_key=True)


class SystemSettingsCreate(SystemSettingsBase):
    """Create request model"""

    pass


class SystemSettingsRead(SystemSettingsBase):
    """Read response model"""

    system_settings_id: UUID


class SystemSettingsUpdate(SystemSettingsBase):
    """Update request model - all optional"""

    pass

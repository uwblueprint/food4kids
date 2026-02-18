from typing import TYPE_CHECKING  # noqa: F401
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel  # noqa: F401

from .base import BaseModel

# if TYPE_CHECKING:
#     from .driver import Driver

MIN_YEAR = 2025
MAX_YEAR = 2100


class DriverHistoryBase(SQLModel):
    """Shared fields between table and API models"""

    driver_id: UUID = Field(foreign_key="drivers.driver_id", index=True)
    year: int = Field(nullable=False, ge=MIN_YEAR, le=MAX_YEAR)
    km: float = Field(nullable=False)


class DriverHistory(DriverHistoryBase, BaseModel, table=True):
    """Database table model"""

    __tablename__ = "driver_history"
    driver_history_id: int | None = Field(default=None, primary_key=True)
    # driver: "Driver" = Relationship(back_populates="history")


class DriverHistoryCreate(DriverHistoryBase):
    """Create request model"""

    pass


class DriverHistoryRead(DriverHistoryBase):
    """Read response model"""

    driver_history_id: int


class DriverHistoryUpdate(SQLModel):
    """Update request model, all fields are required for now since we are only updating km"""

    km: float


class DriverHistorySummary(SQLModel):
    """Summary of driver's lifetime and current year kilometers"""

    lifetime_km: float
    current_year_km: float

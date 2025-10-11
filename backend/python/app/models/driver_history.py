from typing import TYPE_CHECKING  # noqa: F401

from pydantic import field_validator
from sqlmodel import Field, Relationship, SQLModel  # noqa: F401

from .base import BaseModel

# if TYPE_CHECKING:
#     from .driver import Driver

MIN_YEAR = 2025
MAX_YEAR = 2100


class DriverHistoryBase(SQLModel):
    """Shared fields between table and API models"""

    driver_id: int = Field(
        foreign_key="drivers.driver_id", index=True
    )  # TODO FK to driver table, to validate later
    year: int = Field(nullable=False)
    km: float = Field(nullable=False)

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        if not (MIN_YEAR <= v <= MAX_YEAR):
            raise ValueError("Year must be between 2025 and 2100")
        return v


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
    """Update request model - all optional"""

    driver_id: int | None = None
    year: int | None = None
    km: float | None = None

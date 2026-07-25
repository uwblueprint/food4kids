from datetime import date
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from .base import BaseModel

MIN_YEAR = 2025
MAX_YEAR = 2100


class DriverMileageAdjustmentBase(SQLModel):
    """Shared fields between table and API models.

    Driver mileage is derived, not stored: a driver's km for a month is the
    sum of `Route.length` over their frozen routes (those with a
    RouteSnapshot) in that month, plus the signed adjustments here.
    Adjustments cover what routes can't express — manual admin corrections
    and pre-app history. Corrections are new signed entries, never edits.
    """

    # CASCADE: driver deletion is a hard delete, and an adjustment without a
    # driver is unreachable by every query here.
    driver_id: UUID = Field(
        foreign_key="drivers.driver_id", ondelete="CASCADE", index=True
    )
    # The delivery date being corrected; monthly buckets follow this.
    drive_date: date = Field(nullable=False, index=True)
    # Signed: negative entries remove over-credited distance.
    km: float = Field(nullable=False)
    note: str = Field(min_length=1, max_length=1000)


class DriverMileageAdjustment(DriverMileageAdjustmentBase, BaseModel, table=True):
    """Database table model"""

    __tablename__ = "driver_mileage_adjustments"

    adjustment_id: UUID = Field(default_factory=uuid4, primary_key=True)


class DriverMileageAdjustmentCreate(SQLModel):
    """Create request model (admin-only). km is a signed delta."""

    drive_date: date
    km: float
    note: str = Field(min_length=1, max_length=1000)


class DriverMileageAdjustmentRead(DriverMileageAdjustmentBase):
    """Read response model"""

    adjustment_id: UUID


class DriverHistoryRead(SQLModel):
    """One month's km for a driver. Computed, never stored."""

    driver_id: UUID
    year: int
    month: int
    km: float


class DriverHistorySummary(SQLModel):
    """Summary of driver's lifetime and current year kilometers"""

    lifetime_km: float
    current_year_km: float

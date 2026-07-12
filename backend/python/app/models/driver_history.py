from datetime import date
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from .base import BaseModel

MIN_YEAR = 2025
MAX_YEAR = 2100


class DriverMileageAdjustmentBase(SQLModel):
    """Shared fields between table and API models.

    Driver mileage is DERIVED, not stored: a driver's km for a month is the
    sum of `Route.length` over their frozen routes (routes with a
    RouteSnapshot) whose group's drive_date falls in that month, PLUS the
    signed adjustments in this table. Reassigning or editing a route
    therefore updates history automatically — there is no stored total to
    drift out of sync.

    Adjustments exist for what routes can't express: manual admin
    corrections ("Alice actually drove 5 km more") and pre-app history
    migrated from the old monthly-totals table. Corrections are new signed
    entries — never edits — and every entry carries a note explaining why.
    """

    # SET NULL (never CASCADE): corrections are historical facts that must
    # survive driver-row deletion. Soft-delete (Driver.active) means this
    # rarely fires in practice.
    driver_id: UUID | None = Field(
        default=None,
        foreign_key="drivers.driver_id",
        ondelete="SET NULL",
        nullable=True,
        index=True,
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
    """Create request model (admin-only). km is a signed delta and a note
    explaining the correction is required."""

    drive_date: date
    km: float
    note: str = Field(min_length=1, max_length=1000)


class DriverMileageAdjustmentRead(DriverMileageAdjustmentBase):
    """Read response model"""

    adjustment_id: UUID


class DriverHistoryRead(SQLModel):
    """Monthly km read model: SUM(route.length) over the driver's frozen
    routes in that month plus their adjustments. Computed, never stored."""

    driver_id: UUID
    year: int
    month: int
    km: float


class DriverHistorySummary(SQLModel):
    """Summary of driver's lifetime and current year kilometers"""

    lifetime_km: float
    current_year_km: float

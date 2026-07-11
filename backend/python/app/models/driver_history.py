from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import Index, String, text
from sqlmodel import Field, SQLModel

from .base import BaseModel
from .enum import MileageEntryKindEnum

MIN_YEAR = 2025
MAX_YEAR = 2100


class DriverHistoryBase(SQLModel):
    """Shared fields between table and API models.

    driver_history is an append-only LEDGER: one row per mileage event —
    a delivery credited by the nightly freeze job (AUTO), a compensating
    entry when a frozen route's driver changes (REASSIGNMENT), or an admin
    correction (MANUAL_ADJUSTMENT). Rows are never mutated or deleted in
    normal operation; corrections are new signed entries. Monthly and
    lifetime totals are SUM(km) aggregates over this table — there is no
    stored running total to drift out of sync.
    """

    # SET NULL (never CASCADE): the km a driver drove is a historical fact
    # that must survive deletion of the driver row. Soft-delete (Driver.active)
    # means this rarely fires in practice.
    driver_id: UUID | None = Field(
        default=None,
        foreign_key="drivers.driver_id",
        ondelete="SET NULL",
        nullable=True,
        index=True,
    )
    # SET NULL: deleting a past route keeps its mileage (the delivery
    # happened); the entry just loses its route pointer.
    route_id: UUID | None = Field(
        default=None,
        foreign_key="routes.route_id",
        ondelete="SET NULL",
        nullable=True,
        index=True,
    )
    # The delivery date being credited/corrected. Monthly buckets follow
    # this (the month the delivery happened), not the date the entry was
    # posted — late catch-up runs land in the right month.
    drive_date: date = Field(nullable=False, index=True)
    # Signed: negative entries are reversals / downward corrections.
    km: float = Field(nullable=False)
    # Stored as a string column (NOT a native PG enum), matching NoteChain.
    kind: MileageEntryKindEnum = Field(sa_type=String)
    note: str = Field(default="", max_length=1000)


class DriverHistory(DriverHistoryBase, BaseModel, table=True):
    """Database table model"""

    __tablename__ = "driver_history"
    __table_args__ = (
        # Structural no-double-count guard: at most one AUTO credit per route.
        # The freeze job's idempotency check races with nothing thanks to this.
        Index(
            "uq_driver_history_auto_per_route",
            "route_id",
            unique=True,
            postgresql_where=text("kind = 'auto'"),
        ),
    )

    driver_history_id: UUID = Field(default_factory=uuid4, primary_key=True)


class DriverHistoryEntryRead(DriverHistoryBase):
    """Read response model for individual ledger entries (audit view)"""

    driver_history_id: UUID


class DriverHistoryRead(SQLModel):
    """Monthly aggregate read model: SUM(km) over the ledger, bucketed by
    drive_date month. Same response shape as the old monthly-total rows."""

    driver_id: UUID
    year: int
    month: int
    km: float


class DriverHistoryAdjustmentCreate(SQLModel):
    """Create request for a manual mileage adjustment (admin-only).

    Posts a signed MANUAL_ADJUSTMENT ledger entry — corrections never
    overwrite; they append. km is the delta (e.g. -12.5 to remove
    over-credited distance), and a note explaining why is required.
    """

    drive_date: date
    km: float
    note: str = Field(min_length=1, max_length=1000)


class DriverHistorySummary(SQLModel):
    """Summary of driver's lifetime and current year kilometers"""

    lifetime_km: float
    current_year_km: float

"""Per-SKU usage counters for the paid Google APIs route generation calls.

Google's free monthly allowances are granted per SKU and do not pool: spending
Fleet Routing's allowance leaves the Routes API's untouched. Route generation
walks its tiers in quality order, so it needs to know which individual SKU is
exhausted, which one combined total could not answer.

The counter is our own live estimate. The BigQuery billing export is
authoritative but lags hours, far too slow to gate a job that starts now.
"""

from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from .base import BaseModel


class ApiSku(str, Enum):
    """The billable Google SKUs route generation can draw on.

    Values are stored in the database, so renaming one orphans its counter.
    """

    # Route Optimization, two or more vehicles. Billed per *shipment*.
    FLEET_ROUTING = "fleet_routing"
    # Route Optimization, single vehicle. Also billed per shipment.
    SINGLE_VEHICLE_ROUTING = "single_vehicle_routing"
    # Routes API computeRoutes. Billed per *request* — a different unit, and a
    # far larger allowance. Also spent by route polyline lookups.
    ROUTES_COMPUTE = "routes_compute"


class ApiUsageBase(SQLModel):
    # Stored as the SKU's string value rather than a native enum so adding a
    # SKU needs no migration.
    sku: str = Field(max_length=64)
    # "YYYYMM", from ``current_billing_month`` — Google's billing month, which
    # is what the free allowance actually resets on.
    billing_month: str = Field(max_length=6)
    units_used: int = Field(default=0, ge=0)


class ApiUsage(ApiUsageBase, BaseModel, table=True):
    """One row per SKU per billing month.

    The unique constraint is load-bearing: it lets the service upsert
    atomically, so two jobs starting at once cannot each read the same count
    and both decide they have room.
    """

    __tablename__ = "api_usage"
    __table_args__ = (
        UniqueConstraint("sku", "billing_month", name="uq_api_usage_sku_month"),
    )

    api_usage_id: UUID = Field(default_factory=uuid4, primary_key=True)


class ApiUsageRead(ApiUsageBase):
    """A SKU's consumption this month, against its configured allowance."""

    api_usage_id: UUID
    # Carried alongside the count because the allowance lives in settings, not
    # in the row — a caller comparing them needs both.
    budget: int
    remaining: int
    # Units differ per SKU (shipments vs requests), so a bare number is
    # ambiguous without this.
    unit: str

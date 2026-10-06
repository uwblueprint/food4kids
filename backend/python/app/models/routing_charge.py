"""Paid routing requests, estimated at the moment they are sent.

The billing export is the real record of spend but lags by hours, so a burst of
generations would all see the same stale total. These rows cover that gap until
the export catches up; see ``RoutingSpendService``.
"""

from uuid import UUID, uuid4

from sqlmodel import Field

from .base import BaseModel


class RoutingCharge(BaseModel, table=True):
    __tablename__ = "routing_charge"

    routing_charge_id: UUID = Field(default_factory=uuid4, primary_key=True)
    # The cascade tier that sent the request, e.g. "fleet_routing".
    tier: str = Field(max_length=32)
    shipments: int = Field(ge=0)
    # In US dollars at list price, the currency Google prices Maps usage in.
    estimated_cost_usd: float = Field(ge=0)

"""Paid routing requests, estimated when sent. See ``RoutingSpendService``."""

from uuid import UUID, uuid4

from sqlmodel import Field

from .base import BaseModel


class RoutingCharge(BaseModel, table=True):
    __tablename__ = "routing_charge"

    routing_charge_id: UUID = Field(default_factory=uuid4, primary_key=True)
    # e.g. "fleet_routing"
    tier: str = Field(max_length=32)
    shipments: int = Field(ge=0)
    # At list price; Google prices Maps usage in USD.
    estimated_cost_usd: float = Field(ge=0)

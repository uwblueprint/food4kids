from __future__ import annotations

from datetime import datetime  # noqa: TC003 
from uuid import UUID  # noqa: TC003
from typing import TYPE_CHECKING  # noqa: F401

from sqlmodel import SQLModel

if TYPE_CHECKING:
    from datetime import datetime

    from app.models.location_group import LocationGroup


class RouteGenerationSettings(SQLModel):
    """Settings for route generation.
    These are not persisted to the database; used as inputs to services.
    """

    return_to_warehouse: bool = False
    route_start_time: datetime
    num_routes: int
    max_stops_per_route: int | None = None


class RouteGenerationGroupInput(SQLModel):
    """Input bundle for a single location group route generation."""
    location_group_ids: list[UUID]
    settings: RouteGenerationSettings

    model_config = {
        "json_schema_extra": {"examples": [{
            "location_group_ids": ["1bd3890e-1301-47d1-a57a-728bcaa8442d"],
            "settings": {
                "return_to_warehouse": True,
                "route_start_time": "2025-11-05T14:00:00Z",
                "num_routes": 3,
                "max_stops_per_route": 25
            }
        }]}
    }
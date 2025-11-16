from __future__ import annotations

from typing import TYPE_CHECKING

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

    location_group: LocationGroup
    settings: RouteGenerationSettings

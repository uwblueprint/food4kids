from __future__ import annotations

from datetime import datetime  # noqa: TC003

from sqlmodel import SQLModel

from app.models.location_group import LocationGroup  # noqa: TC001


class RouteGenerationSettings(SQLModel):
    """Settings for route generation.

    These are not persisted to the database; used as inputs to services.
    """

    return_to_warehouse: bool = False
    route_start_time: datetime
    num_routes: int
    max_stops_per_route: int | None = None
    service_time_minutes: int = 15


class RouteGenerationGroupInput(SQLModel):
    """Input bundle for a single location group route generation."""

    location_group: LocationGroup
    settings: RouteGenerationSettings

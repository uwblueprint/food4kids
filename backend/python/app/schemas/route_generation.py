from __future__ import annotations

from datetime import datetime  # noqa: TC003

from sqlmodel import Field, SQLModel

from app.models.location_group import LocationGroup  # noqa: TC001


class RouteGenerationSettings(SQLModel):
    """Settings for route generation.

    These are not persisted to the database; used as inputs to services.
    """

    return_to_warehouse: bool = False
    route_start_time: datetime
    num_routes: int
    max_stops_per_route: int | None = None  # Does not apply to Google Maps Routing
    max_half_boxes_per_driver: int = Field(default=28, gt=0)
    # From system settings; used to derive per-location box counts as
    # ceil(num_children / children_per_box). See app.utilities.boxes.
    children_per_box: int = Field(default=2, ge=1)
    service_time_minutes: int = Field(default=15, gt=0)
    route_duration_limit_minutes: int | None = Field(
        default=None,
        gt=0,
        description="Soft cap on total route duration (minutes). "
        "Routes exceeding this incur an optimization penalty to spread "
        "deliveries more evenly.",
    )


class RouteGenerationGroupInput(SQLModel):
    """Input bundle for a single location group route generation."""

    location_group: LocationGroup
    settings: RouteGenerationSettings

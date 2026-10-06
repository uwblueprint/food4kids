from __future__ import annotations

from datetime import datetime  # noqa: TC003

from sqlmodel import Field, SQLModel

from app.models.location_group import LocationGroup  # noqa: TC001


class RouteGenerationSettings(SQLModel):
    """Settings for route generation.

    These are not persisted to the database; used as inputs to services.

    The three configured numbers below — ``max_boxes_per_driver``,
    ``children_per_box`` and ``service_time_minutes`` — are required, with no
    schema-level defaults. They come from the ``system_settings`` row (see
    ``SystemSettings.boxes_per_car`` / ``children_per_box`` /
    ``dropoff_minutes``), and a default here would silently outrank whatever the
    org configured whenever a caller dropped the key. Omitting one is a 422.
    """

    return_to_warehouse: bool = False
    # The moment the drivers leave the warehouse: the group's drive_date
    # combined with SystemSettings.route_start_time (a time of day). Both
    # halves are load-bearing — this anchors the optimizer's globalStartTime,
    # so a wrong date plans the day against the wrong traffic. Naive values are
    # read as warehouse-local time (settings.scheduler_timezone).
    route_start_time: datetime
    num_routes: int
    # SystemSettings.boxes_per_car — the per-car capacity, in boxes.
    max_boxes_per_driver: int = Field(gt=0)
    # SystemSettings.children_per_box; used to derive per-location box counts as
    # ceil(num_children / children_per_box). See app.utilities.boxes.
    children_per_box: int = Field(ge=1)
    # SystemSettings.dropoff_minutes — time spent at each stop. ``ge=0`` mirrors
    # the settings bound: a request must not be rejected for a value the
    # settings screen accepts.
    service_time_minutes: int = Field(ge=0)


class RouteGenerationGroupInput(SQLModel):
    """Input bundle for a single location group route generation."""

    location_group: LocationGroup
    settings: RouteGenerationSettings

from __future__ import annotations

<<<<<<< HEAD
=======
from datetime import datetime  # ruff: noqa: TCH003
>>>>>>> bd5334d (Add error logging)
from typing import TYPE_CHECKING

from sqlmodel import SQLModel

if TYPE_CHECKING:
<<<<<<< HEAD
    from datetime import datetime

=======
>>>>>>> bd5334d (Add error logging)
    from app.models.location_group import LocationGroup


class RouteGenerationSettings(SQLModel):
    """Settings for route generation.
<<<<<<< HEAD

=======
>>>>>>> bd5334d (Add error logging)
    These are not persisted to the database; used as inputs to services.
    """

    return_to_warehouse: bool = False
    route_start_time: datetime
    num_routes: int
    max_stops_per_route: int | None = None


class RouteGenerationGroupInput(SQLModel):
    """Input bundle for a single location group route generation."""

    location_group: LocationGroup
<<<<<<< HEAD
    settings: RouteGenerationSettings
=======
    settings: RouteGenerationSettings
>>>>>>> bd5334d (Add error logging)

"""Runs one claimed route generation job end to end.

Called by the background worker after it has claimed a `PENDING` job and
marked it `RUNNING`. The session is passed in rather than opened here, and
the algorithm is passed in rather than resolved here. That is what makes the
runner testable: tests call it directly with the `test_session` fixture
(whose writes are never committed, so a worker-owned session on another
connection couldn't see them) and a fake algorithm, instead of standing up
a worker.

`run_generation_job` never raises. Every failure is recorded on the job as
`FAILED` with a reason, because a job left sitting in `RUNNING` is a job the
UI waits on forever.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, cast

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import update
from sqlmodel import col, select

from app.models.enum import ProgressEnum
from app.models.job import Job
from app.models.location import Location
from app.models.location_group import LocationGroup
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_stop import RouteStop
from app.models.system_settings import SystemSettings
from app.schemas.route_generation import RouteGenerationGroupInput
from app.services.implementations.route_group_service import (
    ROUTE_GROUP_NAME_MAX_LENGTH,
)
from app.utilities.datetime_utils import now_est_naive
from app.utilities.routes_utils import fetch_route_polyline

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.engine import CursorResult
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.schemas.route_generation import RouteGenerationSettings
    from app.services.protocols.routing_algorithm import RoutingAlgorithmProtocol

logger = logging.getLogger(__name__)

GENERATION_TIMEOUT_SECONDS = 180.0

ENGINE_TIMEOUT_SECONDS = 120.0


class GenerationFailed(Exception):
    """A job that can't go on, carrying a reason worth showing an admin.

    Caught by `run_generation_job`, which stores the message on the job.
    """


async def run_generation_job(
    job_id: UUID,
    session: AsyncSession,
    algorithm: RoutingAlgorithmProtocol,
) -> None:
    """Generate and save the routes one job asked for.

    Ends with the job either `COMPLETED` (with a `RouteGroup` linked and the
    summary recorded) or `FAILED` (with `error_message` set), unless it was
    cancelled along the way, in which case the cancellation stands and
    nothing is saved.
    """
    started = time.perf_counter()
    try:
        job = await _load_running_job(session, job_id)
        if job is None:
            return

        # Idempotency: a prior attempt may have saved the RouteGroup before the
        # process died. Do not call the routing engine again.
        if job.route_group_id is not None:
            await _complete_already_saved(session, job)
            return

        request = _parse_request(job)
        group, locations = await _resolve_locations(session, request.location_group)
        warehouse_lat, warehouse_lon = await _resolve_warehouse(session)

        logger.info(
            "Job %s generating with %s for %d location(s) in group '%s' "
            "(%d route(s) requested).",
            job_id,
            type(algorithm).__name__,
            len(locations),
            group.name,
            request.settings.num_routes,
        )

        async with asyncio.timeout(GENERATION_TIMEOUT_SECONDS):
            engine_started = time.perf_counter()
            clusters = await algorithm.generate_routes(
                locations,
                warehouse_lat,
                warehouse_lon,
                request.settings,
                timeout_seconds=ENGINE_TIMEOUT_SECONDS,
            )
            logger.info(
                "Job %s routing engine finished in %.1fs (%d non-empty cluster(s)).",
                job_id,
                time.perf_counter() - engine_started,
                sum(1 for cluster in clusters if cluster),
            )
            route_group = await _build_route_group(
                group, request.settings, clusters, warehouse_lat, warehouse_lon
            )

        await _save_or_discard(session, job_id, route_group)

    except GenerationFailed as error:
        await _fail(session, job_id, str(error))
    except TimeoutError:
        logger.warning(
            "Job %s hit the %.0fs generation budget after %.1fs.",
            job_id,
            GENERATION_TIMEOUT_SECONDS,
            time.perf_counter() - started,
        )
        await _fail(
            session,
            job_id,
            "Route generation took too long and was stopped. Try again with "
            "fewer locations or routes.",
        )
    except HTTPException as error:
        logger.warning(
            "Job %s routing API error after %.1fs: %s",
            job_id,
            time.perf_counter() - started,
            error.detail,
        )
        await _fail(session, job_id, f"Routing API error: {error.detail}")
    except Exception as error:
        logger.exception(
            "Route generation job %s hit an unexpected error after %.1fs",
            job_id,
            time.perf_counter() - started,
        )
        await _fail(session, job_id, f"Unexpected error: {error}")


async def _load_running_job(session: AsyncSession, job_id: UUID) -> Job | None:
    """Fetch the job, if it is still ours to run."""
    job = (
        await session.execute(select(Job).where(Job.job_id == job_id))
    ).scalar_one_or_none()

    if job is None:
        logger.error("Route generation job %s no longer exists.", job_id)
        return None

    if job.progress != ProgressEnum.RUNNING:
        logger.info(
            "Skipping job %s: no longer Running (now %s), most likely cancelled.",
            job_id,
            job.progress,
        )
        return None

    return job


async def _complete_already_saved(session: AsyncSession, job: Job) -> None:
    """Mark a job Completed when its RouteGroup was already persisted.

    Used when a crash happened after save but before the status flip, or when
    a requeued job is claimed again despite already having a route_group_id.
    """
    now = now_est_naive()
    result = cast(
        "CursorResult[Any]",
        await session.execute(
            update(Job)
            .where(col(Job.job_id) == job.job_id)
            .where(col(Job.progress) == ProgressEnum.RUNNING)
            .values(
                progress=ProgressEnum.COMPLETED,
                error_message=None,
                updated_at=now,
                finished_at=now,
            )
        ),
    )
    if result.rowcount:
        await session.commit()
        logger.info(
            "Job %s completed without regenerating: route_group=%s already saved.",
            job.job_id,
            job.route_group_id,
        )
        return

    await session.rollback()
    logger.info(
        "Job %s already had a RouteGroup but was no longer Running; left unchanged.",
        job.job_id,
    )


def _parse_request(job: Job) -> RouteGenerationGroupInput:
    """Rebuild the request that POST /jobs/generate saved when it queued."""
    if job.input_payload is None:
        raise GenerationFailed("This job was queued without a request to run.")

    try:
        return RouteGenerationGroupInput.model_validate(job.input_payload)
    except ValidationError as error:
        raise GenerationFailed(
            f"The saved generation request could not be read back: {error}"
        ) from error


async def _resolve_locations(
    session: AsyncSession, requested: LocationGroup
) -> tuple[LocationGroup, list[Location]]:
    """Find the location group the admin picked and the locations to route.

    Matched on id first and name second, because `RouteGenerationGroupInput`
    types `location_group` as the table model, whose id defaults to a freshly
    invented UUID. A client that sends only a name and colour, which
    POST /jobs/generate accepts, therefore arrives here with an id matching
    nothing at all. Name is unique and indexed, so it is a safe second key.
    """
    group = (
        await session.execute(
            select(LocationGroup).where(
                LocationGroup.location_group_id == requested.location_group_id
            )
        )
    ).scalar_one_or_none()

    if group is None:
        group = (
            await session.execute(
                select(LocationGroup).where(LocationGroup.name == requested.name)
            )
        ).scalar_one_or_none()

    if group is None:
        raise GenerationFailed(
            f"No location group matches id {requested.location_group_id} or "
            f"name '{requested.name}'."
        )

    locations = (
        (
            await session.execute(
                select(Location).where(
                    Location.location_group_id == group.location_group_id
                )
            )
        )
        .scalars()
        .all()
    )

    routable = [
        location
        for location in locations
        if location.latitude is not None and location.longitude is not None
    ]

    if not routable:
        raise GenerationFailed(
            f"Location group '{group.name}' has no geocoded locations to route."
        )

    if len(routable) < len(locations):
        raise GenerationFailed(
            f"Location group '{group.name}' has {len(locations) - len(routable)} "
            f"location(s) that are not geocoded yet "
            f"({len(routable)} of {len(locations)} are ready). "
            "Geocode every location in the group before generating routes."
        )

    return group, routable


async def _resolve_warehouse(session: AsyncSession) -> tuple[float, float]:
    """Read the depot every route starts from."""
    system_settings = (
        (await session.execute(select(SystemSettings).limit(1))).scalars().first()
    )

    latitude = system_settings.warehouse_latitude if system_settings else None
    longitude = system_settings.warehouse_longitude if system_settings else None

    if latitude is None or longitude is None:
        raise GenerationFailed(
            "Warehouse coordinates are not set in system settings, so there is "
            "nowhere for the routes to start from."
        )

    return latitude, longitude


async def _build_route_group(
    group: LocationGroup,
    settings: RouteGenerationSettings,
    clusters: list[list[Location]],
    warehouse_lat: float,
    warehouse_lon: float,
) -> RouteGroup:
    """Turn the engine's output into a RouteGroup that isn't saved yet.

    The engine only says who rides on which route and in what order; the line
    drawn on the map and the distance come from a second call each, so this
    is one `fetch_route_polyline` per route. Those HTTP calls run concurrently
    via ``asyncio.gather`` so they share the remaining generation timeout
    instead of stacking end-to-end.

    Nothing here touches the session, because the caller may still throw the
    whole thing away if the job was cancelled while these calls were running.
    """
    filled = [cluster for cluster in clusters if cluster]
    if not filled:
        raise GenerationFailed(
            "The routing engine did not place any locations onto a route."
        )

    name = f"{group.name} - {settings.route_start_time:%Y-%m-%d}"
    route_group = RouteGroup(
        name=name[:ROUTE_GROUP_NAME_MAX_LENGTH],
        drive_date=settings.route_start_time.date(),
    )

    polyline_results = await asyncio.gather(
        *(
            fetch_route_polyline(
                locations=cluster,
                warehouse_lat=warehouse_lat,
                warehouse_lon=warehouse_lon,
                ends_at_warehouse=settings.return_to_warehouse,
            )
            for cluster in filled
        )
    )

    for number, (cluster, (encoded_polyline, distance_km)) in enumerate(
        zip(filled, polyline_results, strict=True),
        start=1,
    ):
        route = Route(
            name=f"Route {number}",
            length=distance_km,
            encoded_polyline=encoded_polyline,
            polyline_updated_at=datetime.now(timezone.utc),
            ends_at_warehouse=settings.return_to_warehouse,
            route_group_id=route_group.route_group_id,
        )
        route_group.routes.append(route)

        for stop_number, location in enumerate(cluster, start=1):
            route.route_stops.append(
                RouteStop(
                    route_id=route.route_id,
                    location_id=location.location_id,
                    stop_number=stop_number,
                )
            )

    return route_group


async def _save_or_discard(
    session: AsyncSession, job_id: UUID, route_group: RouteGroup
) -> None:
    """Save the routes and complete the job, or save neither.

    The inserts and the job update share one transaction, and the update only
    matches a job that is still Running. So an admin who cancels while the
    routing engine is working takes the routes with them, instead of leaving
    a RouteGroup attached to a cancelled job, `update_progress` would refuse
    to overwrite the cancellation, and the routes would be stranded.
    """
    session.add(route_group)
    await session.flush()

    routes = route_group.routes
    now = now_est_naive()
    result = cast(
        "CursorResult[Any]",
        await session.execute(
            update(Job)
            .where(col(Job.job_id) == job_id)
            .where(col(Job.progress) == ProgressEnum.RUNNING)
            .values(
                progress=ProgressEnum.COMPLETED,
                route_group_id=route_group.route_group_id,
                error_message=None,
                routes_created=len(routes),
                total_stops=sum(len(route.route_stops) for route in routes),
                total_distance_km=sum(route.length for route in routes),
                total_families=len(
                    {stop.location_id for route in routes for stop in route.route_stops}
                ),
                updated_at=now,
                finished_at=now,
            )
        ),
    )

    if not result.rowcount:
        logger.info(
            "Job %s stopped being Running while it generated, most likely "
            "cancelled; discarding its %d route(s).",
            job_id,
            len(routes),
        )
        await session.rollback()
        return

    await session.commit()
    logger.info(
        "Job %s completed: route_group=%s routes=%d stops=%d.",
        job_id,
        route_group.route_group_id,
        len(routes),
        sum(len(route.route_stops) for route in routes),
    )


async def _fail(session: AsyncSession, job_id: UUID, message: str) -> None:
    """Undo anything half-written, then record why the job failed.

    Guarded the same way `JobService.update_progress` is, so a job an admin
    already cancelled stays cancelled instead of resurfacing as a failure.
    """
    logger.warning("Route generation job %s failed: %s", job_id, message)

    await session.rollback()
    now = now_est_naive()
    result = cast(
        "CursorResult[Any]",
        await session.execute(
            update(Job)
            .where(col(Job.job_id) == job_id)
            .where(col(Job.progress) == ProgressEnum.RUNNING)
            .values(
                progress=ProgressEnum.FAILED,
                error_message=message,
                updated_at=now,
                finished_at=now,
            )
        ),
    )
    await session.commit()
    if not result.rowcount:
        logger.warning(
            "Job %s failure was not recorded: it was no longer Running "
            "(likely cancelled).",
            job_id,
        )

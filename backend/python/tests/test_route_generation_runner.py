"""Tests for the route generation runner.

These call `run_generation_job` the way the future worker loop will — with a
session and an algorithm handed to it — so the whole pipeline is exercised
without a worker, and without reaching Google: the algorithm is a fake and
`fetch_route_polyline` is patched out for every test in this file.
"""

from __future__ import annotations

import asyncio
import inspect
from datetime import datetime
from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlmodel import col, select

from app.models.enum import ProgressEnum
from app.models.job import Job
from app.models.location import Location
from app.models.location_group import LocationGroup
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_stop import RouteStop
from app.models.system_settings import SystemSettings
from app.schemas.route_generation import (
    RouteGenerationGroupInput,
    RouteGenerationSettings,
)
from app.services.implementations import route_generation_runner as runner
from app.services.implementations.route_generation_runner import run_generation_job

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.ext.asyncio import AsyncSession

WAREHOUSE_LAT = 43.6532
WAREHOUSE_LON = -79.3832
POLYLINE_KM = 12.5
DRIVE_DATE = datetime(2026, 6, 1, 8, 0)


class FakeRoutingAlgorithm:
    """Stands in for the real engine. `plan` decides what one call does:
    return clusters, return an awaitable, or raise."""

    def __init__(self, plan: Callable[[list[Location]], Any]) -> None:
        self._plan = plan
        self.calls = 0
        self.timeout_seconds: float | None = None

    async def generate_routes(
        self,
        locations: list[Location],
        warehouse_lat: float,  # noqa: ARG002
        warehouse_lon: float,  # noqa: ARG002
        settings: RouteGenerationSettings,  # noqa: ARG002
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:
        self.calls += 1
        self.timeout_seconds = timeout_seconds
        outcome: Any = self._plan(locations)
        if inspect.isawaitable(outcome):
            outcome = await outcome
        return cast("list[list[Location]]", outcome)


def _never_called(_locations: list[Location]) -> Any:
    pytest.fail("the routing engine should not have been reached")


@pytest.fixture(autouse=True)
def fake_polyline(monkeypatch: pytest.MonkeyPatch) -> None:
    """No test in this file may reach the real Google Maps API."""

    async def _fetch(**_kwargs: Any) -> tuple[str, float]:
        return "fake-polyline", POLYLINE_KM

    monkeypatch.setattr(runner, "fetch_route_polyline", _fetch)


async def _add_group(session: AsyncSession, name: str = "Test Group") -> LocationGroup:
    group = LocationGroup(name=name, color="#FF5733")
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return group


async def _add_location(
    session: AsyncSession,
    group: LocationGroup,
    name: str,
    *,
    latitude: float | None = 43.7,
    longitude: float | None = -79.4,
) -> Location:
    location = Location(
        location_group_id=group.location_group_id,
        name=name,
        contact_name=name,
        address=f"{name} Street",
        phone_primary="5550000000",
        delivery_type="Family",
        latitude=latitude,
        longitude=longitude,
    )
    session.add(location)
    await session.commit()
    await session.refresh(location)
    return location


async def _add_warehouse(session: AsyncSession, *, configured: bool = True) -> None:
    session.add(
        SystemSettings(
            warehouse_latitude=WAREHOUSE_LAT if configured else None,
            warehouse_longitude=WAREHOUSE_LON if configured else None,
        )
    )
    await session.commit()


async def _queue_running_job(
    session: AsyncSession, requested_group: LocationGroup, *, num_routes: int = 2
) -> Job:
    """A job in the state the worker hands to the runner: claimed (Running)
    with the request it was queued with saved on it."""
    request = RouteGenerationGroupInput(
        location_group=requested_group,
        settings=RouteGenerationSettings(
            route_start_time=DRIVE_DATE, num_routes=num_routes
        ),
    )
    job = Job(
        progress=ProgressEnum.RUNNING,
        input_payload=request.model_dump(mode="json"),
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def _route_groups(session: AsyncSession) -> list[RouteGroup]:
    return list((await session.execute(select(RouteGroup))).scalars().all())


class TestSuccessfulGeneration:
    @pytest.mark.asyncio
    async def test_saves_routes_and_records_the_summary(
        self, test_session: AsyncSession
    ) -> None:
        """The happy path: engine output becomes a RouteGroup with ordered
        stops, and the job completes carrying the summary numbers."""
        group = await _add_group(test_session)
        first = await _add_location(test_session, group, "Family A")
        second = await _add_location(test_session, group, "Family B")
        third = await _add_location(test_session, group, "Family C")
        await _add_warehouse(test_session)
        job = await _queue_running_job(test_session, group)

        algorithm = FakeRoutingAlgorithm(lambda _locations: [[first, second], [third]])
        await run_generation_job(job.job_id, test_session, algorithm)

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.COMPLETED
        assert job.error_message is None
        assert job.finished_at is not None
        assert job.route_group_id is not None
        assert job.routes_created == 2
        assert job.total_stops == 3
        assert job.total_distance_km == pytest.approx(2 * POLYLINE_KM)
        assert job.total_families == 3

        route_group = (
            await test_session.execute(
                select(RouteGroup).where(
                    RouteGroup.route_group_id == job.route_group_id
                )
            )
        ).scalar_one()
        assert route_group.name == "Test Group - 2026-06-01"
        assert route_group.drive_date == DRIVE_DATE

        routes = (
            (
                await test_session.execute(
                    select(Route)
                    .where(Route.route_group_id == route_group.route_group_id)
                    .order_by(Route.name)
                )
            )
            .scalars()
            .all()
        )
        assert [route.name for route in routes] == ["Route 1", "Route 2"]
        assert all(route.encoded_polyline == "fake-polyline" for route in routes)
        assert all(route.length == pytest.approx(POLYLINE_KM) for route in routes)
        assert all(route.driver_id is None for route in routes)

        stops = (
            (
                await test_session.execute(
                    select(RouteStop)
                    .where(RouteStop.route_id == routes[0].route_id)
                    .order_by(col(RouteStop.stop_number))
                )
            )
            .scalars()
            .all()
        )
        assert [stop.stop_number for stop in stops] == [1, 2]
        assert [stop.location_id for stop in stops] == [
            first.location_id,
            second.location_id,
        ]

    @pytest.mark.asyncio
    async def test_finds_the_group_by_name_when_the_id_is_made_up(
        self, test_session: AsyncSession
    ) -> None:
        """A request that carried only a name still resolves: Pydantic
        invents an id for it, and that id matches nothing."""
        group = await _add_group(test_session)
        location = await _add_location(test_session, group, "Family A")
        await _add_warehouse(test_session)
        job = await _queue_running_job(
            test_session,
            LocationGroup(name=group.name, color=group.color),
            num_routes=1,
        )

        algorithm = FakeRoutingAlgorithm(lambda _locations: [[location]])
        await run_generation_job(job.job_id, test_session, algorithm)

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.COMPLETED
        assert job.routes_created == 1

    @pytest.mark.asyncio
    async def test_routes_only_the_geocoded_locations(
        self, test_session: AsyncSession
    ) -> None:
        """A location without coordinates is skipped, not fatal."""
        group = await _add_group(test_session)
        geocoded = await _add_location(test_session, group, "Family A")
        await _add_location(
            test_session, group, "Family B", latitude=None, longitude=None
        )
        await _add_warehouse(test_session)
        job = await _queue_running_job(test_session, group, num_routes=1)

        seen: list[list[Location]] = []

        def _plan(locations: list[Location]) -> Any:
            seen.append(locations)
            return [locations]

        await run_generation_job(job.job_id, test_session, FakeRoutingAlgorithm(_plan))

        assert [location.location_id for location in seen[0]] == [geocoded.location_id]
        await test_session.refresh(job)
        assert job.progress == ProgressEnum.COMPLETED
        assert job.total_families == 1

    @pytest.mark.asyncio
    async def test_empty_clusters_do_not_become_routes(
        self, test_session: AsyncSession
    ) -> None:
        """Asking for more routes than the engine can fill leaves empty
        clusters, and an empty route is not worth saving."""
        group = await _add_group(test_session)
        location = await _add_location(test_session, group, "Family A")
        await _add_warehouse(test_session)
        job = await _queue_running_job(test_session, group, num_routes=3)

        algorithm = FakeRoutingAlgorithm(lambda _locations: [[location], [], []])
        await run_generation_job(job.job_id, test_session, algorithm)

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.COMPLETED
        assert job.routes_created == 1
        assert job.total_stops == 1

    @pytest.mark.asyncio
    async def test_the_engine_is_given_a_timeout(
        self, test_session: AsyncSession
    ) -> None:
        """One hung call would stall every later job, so the engine never
        gets to run unbounded."""
        group = await _add_group(test_session)
        location = await _add_location(test_session, group, "Family A")
        await _add_warehouse(test_session)
        job = await _queue_running_job(test_session, group, num_routes=1)

        algorithm = FakeRoutingAlgorithm(lambda _locations: [[location]])
        await run_generation_job(job.job_id, test_session, algorithm)

        assert algorithm.timeout_seconds == runner.ENGINE_TIMEOUT_SECONDS


class TestFailedGeneration:
    @pytest.mark.asyncio
    async def test_engine_error_fails_the_job_and_saves_nothing(
        self, test_session: AsyncSession
    ) -> None:
        group = await _add_group(test_session)
        await _add_location(test_session, group, "Family A")
        await _add_warehouse(test_session)
        job = await _queue_running_job(test_session, group)

        def _explode(_locations: list[Location]) -> Any:
            raise RuntimeError("the engine fell over")

        await run_generation_job(
            job.job_id, test_session, FakeRoutingAlgorithm(_explode)
        )

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.FAILED
        assert job.error_message is not None
        assert "the engine fell over" in job.error_message
        assert job.route_group_id is None
        assert await _route_groups(test_session) == []

    @pytest.mark.asyncio
    async def test_engine_timeout_fails_the_job(
        self, test_session: AsyncSession
    ) -> None:
        group = await _add_group(test_session)
        await _add_location(test_session, group, "Family A")
        await _add_warehouse(test_session)
        job = await _queue_running_job(test_session, group)

        def _time_out(_locations: list[Location]) -> Any:
            raise TimeoutError

        await run_generation_job(
            job.job_id, test_session, FakeRoutingAlgorithm(_time_out)
        )

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.FAILED
        assert "too long" in (job.error_message or "")

    @pytest.mark.asyncio
    async def test_overall_budget_covers_the_polyline_calls_too(
        self, test_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The engine returning in time is not enough: the polyline calls
        that follow are inside the same budget."""
        group = await _add_group(test_session)
        location = await _add_location(test_session, group, "Family A")
        await _add_warehouse(test_session)
        job = await _queue_running_job(test_session, group, num_routes=1)

        async def _slow_polyline(**_kwargs: Any) -> tuple[str, float]:
            await asyncio.sleep(5)
            return "never-gets-here", 1.0

        monkeypatch.setattr(runner, "fetch_route_polyline", _slow_polyline)
        monkeypatch.setattr(runner, "GENERATION_TIMEOUT_SECONDS", 0.05)

        algorithm = FakeRoutingAlgorithm(lambda _locations: [[location]])
        await run_generation_job(job.job_id, test_session, algorithm)

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.FAILED
        assert "too long" in (job.error_message or "")
        assert await _route_groups(test_session) == []

    @pytest.mark.asyncio
    async def test_polyline_api_error_fails_the_job(
        self, test_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """fetch_route_polyline raises HTTP exceptions because of where it
        usually runs; here there is no request, only a failed job."""
        group = await _add_group(test_session)
        location = await _add_location(test_session, group, "Family A")
        await _add_warehouse(test_session)
        job = await _queue_running_job(test_session, group, num_routes=1)

        async def _unavailable(**_kwargs: Any) -> tuple[str, float]:
            raise HTTPException(status_code=503, detail="Google Maps API error: nope")

        monkeypatch.setattr(runner, "fetch_route_polyline", _unavailable)

        algorithm = FakeRoutingAlgorithm(lambda _locations: [[location]])
        await run_generation_job(job.job_id, test_session, algorithm)

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.FAILED
        assert "Google Maps API error: nope" in (job.error_message or "")
        assert await _route_groups(test_session) == []

    @pytest.mark.asyncio
    async def test_unset_warehouse_fails_before_calling_the_engine(
        self, test_session: AsyncSession
    ) -> None:
        group = await _add_group(test_session)
        await _add_location(test_session, group, "Family A")
        await _add_warehouse(test_session, configured=False)
        job = await _queue_running_job(test_session, group)

        algorithm = FakeRoutingAlgorithm(_never_called)
        await run_generation_job(job.job_id, test_session, algorithm)

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.FAILED
        assert "Warehouse coordinates" in (job.error_message or "")
        assert algorithm.calls == 0

    @pytest.mark.asyncio
    async def test_missing_system_settings_fails_the_job(
        self, test_session: AsyncSession
    ) -> None:
        """A database with no settings row at all reads the same as one with
        no warehouse set."""
        group = await _add_group(test_session)
        await _add_location(test_session, group, "Family A")
        job = await _queue_running_job(test_session, group)

        algorithm = FakeRoutingAlgorithm(_never_called)
        await run_generation_job(job.job_id, test_session, algorithm)

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.FAILED
        assert "Warehouse coordinates" in (job.error_message or "")

    @pytest.mark.asyncio
    async def test_unknown_location_group_fails_the_job(
        self, test_session: AsyncSession
    ) -> None:
        """The group can be deleted between queueing and running."""
        await _add_warehouse(test_session)
        job = await _queue_running_job(
            test_session, LocationGroup(name="Ghost Group", color="#000000")
        )

        algorithm = FakeRoutingAlgorithm(_never_called)
        await run_generation_job(job.job_id, test_session, algorithm)

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.FAILED
        assert "Ghost Group" in (job.error_message or "")
        assert algorithm.calls == 0

    @pytest.mark.asyncio
    async def test_group_without_geocoded_locations_fails_the_job(
        self, test_session: AsyncSession
    ) -> None:
        group = await _add_group(test_session)
        await _add_location(
            test_session, group, "Family A", latitude=None, longitude=None
        )
        await _add_warehouse(test_session)
        job = await _queue_running_job(test_session, group)

        algorithm = FakeRoutingAlgorithm(_never_called)
        await run_generation_job(job.job_id, test_session, algorithm)

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.FAILED
        assert "no geocoded locations" in (job.error_message or "")

    @pytest.mark.asyncio
    async def test_engine_returning_nothing_fails_the_job(
        self, test_session: AsyncSession
    ) -> None:
        group = await _add_group(test_session)
        await _add_location(test_session, group, "Family A")
        await _add_warehouse(test_session)
        job = await _queue_running_job(test_session, group, num_routes=1)

        algorithm = FakeRoutingAlgorithm(lambda _locations: [])
        await run_generation_job(job.job_id, test_session, algorithm)

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.FAILED
        assert "did not place any locations" in (job.error_message or "")
        assert await _route_groups(test_session) == []

    @pytest.mark.asyncio
    async def test_job_without_a_saved_request_fails(
        self, test_session: AsyncSession
    ) -> None:
        job = Job(progress=ProgressEnum.RUNNING)
        test_session.add(job)
        await test_session.commit()
        await test_session.refresh(job)

        algorithm = FakeRoutingAlgorithm(_never_called)
        await run_generation_job(job.job_id, test_session, algorithm)

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.FAILED
        assert "without a request" in (job.error_message or "")

    @pytest.mark.asyncio
    async def test_unreadable_saved_request_fails(
        self, test_session: AsyncSession
    ) -> None:
        job = Job(progress=ProgressEnum.RUNNING, input_payload={"nonsense": True})
        test_session.add(job)
        await test_session.commit()
        await test_session.refresh(job)

        algorithm = FakeRoutingAlgorithm(_never_called)
        await run_generation_job(job.job_id, test_session, algorithm)

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.FAILED
        assert "could not be read back" in (job.error_message or "")


class TestJobsItShouldNotTouch:
    @pytest.mark.asyncio
    async def test_a_job_that_is_not_running_is_left_alone(
        self, test_session: AsyncSession
    ) -> None:
        """The worker claims a job before handing it over, so anything else
        belongs to someone else."""
        job = Job(progress=ProgressEnum.PENDING)
        test_session.add(job)
        await test_session.commit()
        await test_session.refresh(job)

        algorithm = FakeRoutingAlgorithm(_never_called)
        await run_generation_job(job.job_id, test_session, algorithm)

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.PENDING
        assert job.error_message is None

    @pytest.mark.asyncio
    async def test_a_missing_job_is_not_an_error(
        self, test_session: AsyncSession
    ) -> None:
        await run_generation_job(
            uuid4(), test_session, FakeRoutingAlgorithm(_never_called)
        )

    @pytest.mark.asyncio
    async def test_cancelling_mid_flight_discards_the_routes(
        self, test_session: AsyncSession
    ) -> None:
        """An admin cancelling while the engine works takes the routes with
        them: a RouteGroup left behind would be attached to a cancelled job
        that can never be marked complete."""
        group = await _add_group(test_session)
        location = await _add_location(test_session, group, "Family A")
        location_id = location.location_id
        await _add_warehouse(test_session)
        job = await _queue_running_job(test_session, group, num_routes=1)

        async def _cancel_then_answer(
            locations: list[Location],
        ) -> list[list[Location]]:
            cancelled = await test_session.execute(
                select(Job).where(Job.job_id == job.job_id)
            )
            cancelled.scalar_one().progress = ProgressEnum.CANCELLED
            await test_session.commit()
            return [locations]

        await run_generation_job(
            job.job_id, test_session, FakeRoutingAlgorithm(_cancel_then_answer)
        )

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.CANCELLED
        assert job.route_group_id is None
        assert job.routes_created is None
        assert await _route_groups(test_session) == []
        assert (await test_session.execute(select(Route))).scalars().first() is None
        # Only the generated routes are rolled back. The locations the job read
        # on its way there were committed before it started and must survive.
        assert (
            await test_session.execute(
                select(Location).where(Location.location_id == location_id)
            )
        ).scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_cancelling_mid_flight_survives_a_failure(
        self, test_session: AsyncSession
    ) -> None:
        """A job cancelled while the engine was failing stays cancelled
        rather than being reopened as a failure."""
        group = await _add_group(test_session)
        await _add_location(test_session, group, "Family A")
        await _add_warehouse(test_session)
        job = await _queue_running_job(test_session, group, num_routes=1)

        async def _cancel_then_explode(_locations: list[Location]) -> Any:
            cancelled = await test_session.execute(
                select(Job).where(Job.job_id == job.job_id)
            )
            cancelled.scalar_one().progress = ProgressEnum.CANCELLED
            await test_session.commit()
            raise RuntimeError("too late")

        await run_generation_job(
            job.job_id, test_session, FakeRoutingAlgorithm(_cancel_then_explode)
        )

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.CANCELLED
        assert job.error_message is None

"""Tests for the route generation background worker.

The worker opens its own sessions via the module-global session maker, so
these tests point that global at the test engine (same pattern as the
route-freeze job tests) and seed committed rows the worker can see.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import select

from app.models.enum import ProgressEnum
from app.models.job import Job
from app.models.location import Location
from app.models.location_group import LocationGroup
from app.models.route_group import RouteGroup
from app.models.system_settings import SystemSettings
from app.schemas.route_generation import (
    RouteGenerationGroupInput,
    RouteGenerationSettings,
)
from app.services.implementations import route_generation_runner as runner
from app.services.implementations import route_generation_worker as worker
from app.services.implementations.job_service import JobService
from app.services.implementations.route_generation_worker import (
    RECOVERY_ERROR_MESSAGE,
    claim_next_pending_job,
    recover_route_generation_jobs,
    start_route_generation_worker,
    stop_route_generation_worker,
    wake_route_generation_worker,
)

if TYPE_CHECKING:
    from collections.abc import Callable

WAREHOUSE_LAT = 43.6532
WAREHOUSE_LON = -79.3832
DRIVE_DATE = datetime(2026, 6, 1, 8, 0)


class FakeRoutingAlgorithm:
    def __init__(self, plan: Callable[[list[Location]], Any]) -> None:
        self._plan = plan
        self.calls = 0

    async def generate_routes(
        self,
        locations: list[Location],
        warehouse_lat: float,  # noqa: ARG002
        warehouse_lon: float,  # noqa: ARG002
        settings: RouteGenerationSettings,  # noqa: ARG002
        timeout_seconds: float | None = None,  # noqa: ARG002
    ) -> list[list[Location]]:
        self.calls += 1
        return self._plan(locations)


def _maker(test_db_engine: Any) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture(autouse=True)
def reset_worker_state() -> Any:
    """Each test gets a fresh doorbell and no leftover worker task."""
    worker._wake_event = asyncio.Event()
    worker._worker_task = None
    yield
    task = worker._worker_task
    worker._worker_task = None
    if task is not None and not task.done():
        task.cancel()


@pytest.fixture(autouse=True)
def fake_polyline(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fetch(**_kwargs: Any) -> tuple[str, float]:
        return "fake-polyline", 12.5

    monkeypatch.setattr(runner, "fetch_route_polyline", _fetch)


async def _seed_routable_group(
    maker: async_sessionmaker[AsyncSession],
) -> tuple[LocationGroup, Location]:
    async with maker() as session:
        group = LocationGroup(name="Worker Group", color="#FF5733")
        session.add(group)
        await session.commit()
        await session.refresh(group)

        location = Location(
            location_group_id=group.location_group_id,
            name="Family A",
            contact_name="Family A",
            address="1 Test St",
            phone_primary="5550000000",
            delivery_type="Family",
            latitude=43.7,
            longitude=-79.4,
        )
        session.add(
            SystemSettings(
                warehouse_latitude=WAREHOUSE_LAT,
                warehouse_longitude=WAREHOUSE_LON,
            )
        )
        session.add(location)
        await session.commit()
        await session.refresh(location)
        return group, location


async def _queue_pending_job(
    maker: async_sessionmaker[AsyncSession], group: LocationGroup
) -> Job:
    request = RouteGenerationGroupInput(
        location_group=group,
        settings=RouteGenerationSettings(route_start_time=DRIVE_DATE, num_routes=1),
    )
    async with maker() as session:
        job = Job(
            progress=ProgressEnum.PENDING,
            input_payload=request.model_dump(mode="json"),
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job


class TestClaimAndRecover:
    @pytest.mark.asyncio
    async def test_claim_takes_oldest_pending(self, test_db_engine: Any) -> None:
        maker = _maker(test_db_engine)
        async with maker() as session:
            older = Job(progress=ProgressEnum.PENDING)
            newer = Job(progress=ProgressEnum.PENDING)
            session.add(older)
            await session.commit()
            await session.refresh(older)
            session.add(newer)
            await session.commit()
            await session.refresh(newer)

            claimed = await claim_next_pending_job(session)
            assert claimed == older.job_id

            await session.refresh(older)
            await session.refresh(newer)
            assert older.progress == ProgressEnum.RUNNING
            assert older.started_at is not None
            assert newer.progress == ProgressEnum.PENDING

    @pytest.mark.asyncio
    async def test_claim_returns_none_when_queue_empty(
        self, test_db_engine: Any
    ) -> None:
        maker = _maker(test_db_engine)
        async with maker() as session:
            assert await claim_next_pending_job(session) is None

    @pytest.mark.asyncio
    async def test_claim_skips_non_pending_jobs(self, test_db_engine: Any) -> None:
        maker = _maker(test_db_engine)
        async with maker() as session:
            session.add(Job(progress=ProgressEnum.CANCELLED))
            session.add(Job(progress=ProgressEnum.COMPLETED))
            await session.commit()
            assert await claim_next_pending_job(session) is None

    @pytest.mark.asyncio
    async def test_recover_fails_running_and_wakes_for_pending(
        self, test_db_engine: Any
    ) -> None:
        maker = _maker(test_db_engine)
        async with maker() as session:
            running = Job(progress=ProgressEnum.RUNNING)
            pending = Job(progress=ProgressEnum.PENDING)
            session.add(running)
            session.add(pending)
            await session.commit()
            await session.refresh(running)
            await session.refresh(pending)

            assert not worker._wake_event.is_set()
            await recover_route_generation_jobs(session)

            await session.refresh(running)
            await session.refresh(pending)
            assert running.progress == ProgressEnum.FAILED
            assert running.error_message == RECOVERY_ERROR_MESSAGE
            assert running.finished_at is not None
            assert pending.progress == ProgressEnum.PENDING
            assert worker._wake_event.is_set()

    @pytest.mark.asyncio
    async def test_recover_does_not_wake_when_nothing_pending(
        self, test_db_engine: Any
    ) -> None:
        maker = _maker(test_db_engine)
        async with maker() as session:
            session.add(Job(progress=ProgressEnum.RUNNING))
            await session.commit()
            await recover_route_generation_jobs(session)
            assert not worker._wake_event.is_set()


class TestEnqueueDoorbell:
    @pytest.mark.asyncio
    async def test_enqueue_pending_job_wakes_worker(
        self, test_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        wakes: list[bool] = []
        monkeypatch.setattr(
            "app.services.implementations.job_service.wake_route_generation_worker",
            lambda: wakes.append(True),
        )

        job = Job(progress=ProgressEnum.PENDING)
        test_session.add(job)
        await test_session.commit()
        await test_session.refresh(job)

        service = JobService(logger=logging.getLogger("test"), session=test_session)
        await service.enqueue(job.job_id)

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.PENDING
        assert wakes == [True]

    @pytest.mark.asyncio
    async def test_enqueue_cancelled_job_does_not_wake(
        self, test_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        wakes: list[bool] = []
        monkeypatch.setattr(
            "app.services.implementations.job_service.wake_route_generation_worker",
            lambda: wakes.append(True),
        )

        job = Job(progress=ProgressEnum.CANCELLED)
        test_session.add(job)
        await test_session.commit()
        await test_session.refresh(job)

        service = JobService(logger=logging.getLogger("test"), session=test_session)
        await service.enqueue(job.job_id)

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.CANCELLED
        assert wakes == []


class TestWorkerLoop:
    @pytest.mark.asyncio
    async def test_worker_claims_and_completes_a_pending_job(
        self, test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        maker = _maker(test_db_engine)
        monkeypatch.setattr("app.models.async_session_maker_instance", maker)

        group, location = await _seed_routable_group(maker)
        job = await _queue_pending_job(maker, group)

        algorithm = FakeRoutingAlgorithm(lambda locations: [locations])
        monkeypatch.setattr(worker, "get_routing_algorithm", lambda: algorithm)

        start_route_generation_worker()
        wake_route_generation_worker()

        async with maker() as session:
            for _ in range(50):
                session.expire_all()
                refreshed = (
                    await session.execute(select(Job).where(Job.job_id == job.job_id))
                ).scalar_one()
                if refreshed.progress in {
                    ProgressEnum.COMPLETED,
                    ProgressEnum.FAILED,
                }:
                    break
                await asyncio.sleep(0.05)
            else:
                pytest.fail("worker did not finish the job in time")

            assert refreshed.progress == ProgressEnum.COMPLETED
            assert refreshed.route_group_id is not None
            assert algorithm.calls == 1
            assert (
                await session.execute(
                    select(RouteGroup).where(
                        RouteGroup.route_group_id == refreshed.route_group_id
                    )
                )
            ).scalar_one_or_none() is not None
            assert location.latitude is not None

        await stop_route_generation_worker()

    @pytest.mark.asyncio
    async def test_worker_drains_multiple_pending_jobs(
        self, test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        maker = _maker(test_db_engine)
        monkeypatch.setattr("app.models.async_session_maker_instance", maker)

        group, _location = await _seed_routable_group(maker)
        first = await _queue_pending_job(maker, group)
        second = await _queue_pending_job(maker, group)

        algorithm = FakeRoutingAlgorithm(lambda locations: [locations])
        monkeypatch.setattr(worker, "get_routing_algorithm", lambda: algorithm)

        start_route_generation_worker()
        wake_route_generation_worker()

        async with maker() as session:
            for _ in range(80):
                session.expire_all()
                jobs = (
                    (
                        await session.execute(
                            select(Job).where(
                                Job.job_id.in_([first.job_id, second.job_id])
                            )
                        )
                    )
                    .scalars()
                    .all()
                )
                if all(job.progress == ProgressEnum.COMPLETED for job in jobs):
                    break
                await asyncio.sleep(0.05)
            else:
                pytest.fail("worker did not drain both jobs in time")

            assert algorithm.calls == 2

        await stop_route_generation_worker()

    @pytest.mark.asyncio
    async def test_stop_cancels_an_idle_worker(self) -> None:
        task = start_route_generation_worker()
        assert not task.done()
        await stop_route_generation_worker()
        assert task.done()
        assert worker._worker_task is None

"""Background consumer for route generation jobs.

One long-lived asyncio task sleeps on a wake event until
``POST /jobs/generate`` wakes the worker, then claims ``PENDING`` jobs one
at a time and hands each to ``run_generation_job``. The ``jobs`` table is the
durable queue; the event is only an in-memory signal, so a process restart
needs the startup sweep to repair orphaned ``RUNNING`` rows (complete,
requeue, or fail) and re-ring if any ``PENDING`` work is waiting.

Assumes a single process runs this worker. The drain loop treats a failed claim
(``None``) as "queue empty" and stops. With multiple uvicorn/gunicorn workers
or replicas, a lost claim race can also return ``None`` while ``PENDING`` jobs
remain, leaving them stuck until the next ``POST /jobs/generate`` wake.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import update
from sqlmodel import col, select

from app import models as app_models
from app.dependencies.services import get_routing_algorithm
from app.models.enum import ProgressEnum
from app.models.job import Job
from app.services.implementations.route_generation_runner import run_generation_job
from app.utilities.datetime_utils import now_utc

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.engine import CursorResult
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_wake_event = asyncio.Event()
_worker_task: asyncio.Task[None] | None = None

# One automatic return to PENDING after a crash; a second orphan fails.
MAX_AUTO_REQUEUE_ATTEMPTS = 1

RECOVERY_ERROR_MESSAGE = (
    "Route generation was interrupted because the server restarted and "
    "could not be automatically retried. Enqueue the job again."
)


def wake_route_generation_worker() -> None:
    """Wake the worker so it looks for PENDING jobs."""
    _wake_event.set()


async def claim_next_pending_job(session: AsyncSession) -> UUID | None:
    """Atomically take the oldest PENDING job and mark it RUNNING.

    The progress check is in the UPDATE itself, so two workers (or a cancel
    racing the claim) cannot both start the same job: zero rows updated means
    someone else got there first.
    """
    now = now_utc()
    oldest_pending = (
        select(Job.job_id)
        .where(col(Job.progress) == ProgressEnum.PENDING)
        .order_by(col(Job.created_at).asc(), col(Job.job_id).asc())
        .limit(1)
        .scalar_subquery()
    )
    result = await session.execute(
        update(Job)
        .where(col(Job.job_id) == oldest_pending)
        .where(col(Job.progress) == ProgressEnum.PENDING)
        .values(
            progress=ProgressEnum.RUNNING,
            started_at=now,
            updated_at=now,
        )
        .returning(col(Job.job_id))
    )
    job_id = result.scalar_one_or_none()
    if job_id is None:
        await session.rollback()
        return None

    await session.commit()
    return job_id


async def recover_route_generation_jobs(session: AsyncSession) -> None:
    """Repair jobs left RUNNING across a restart, and wake if PENDING remain.

    A RUNNING job cannot resume its in-flight Google call — that connection is
    gone. Recovery instead:

    1. If ``route_group_id`` is already set, mark COMPLETED. Unreachable while
       ``_save_or_discard`` commits the RouteGroup and status together; kept as
       a belt-and-suspenders guard if that assumption changes.
    2. Else if ``retry_count`` is under the auto-requeue cap, return the job
       to PENDING so the worker retries from ``input_payload``.
    3. Else mark FAILED so a crash loop cannot requeue forever.

    Leaving orphans in RUNNING would make the UI wait forever.
    """
    now = now_utc()

    completed = cast(
        "CursorResult[Any]",
        await session.execute(
            # Defensive: not expected while RouteGroup + COMPLETED share one commit.
            update(Job)
            .where(col(Job.progress) == ProgressEnum.RUNNING)
            .where(col(Job.route_group_id).is_not(None))
            .values(
                progress=ProgressEnum.COMPLETED,
                error_message=None,
                updated_at=now,
                finished_at=now,
            )
        ),
    )
    if completed.rowcount:
        logger.info(
            "Marked %d interrupted route generation job(s) as Completed after "
            "restart (RouteGroup already saved).",
            completed.rowcount,
        )

    requeued = cast(
        "CursorResult[Any]",
        await session.execute(
            update(Job)
            .where(col(Job.progress) == ProgressEnum.RUNNING)
            .where(col(Job.route_group_id).is_(None))
            .where(col(Job.retry_count) < MAX_AUTO_REQUEUE_ATTEMPTS)
            .values(
                progress=ProgressEnum.PENDING,
                retry_count=col(Job.retry_count) + 1,
                started_at=None,
                error_message=None,
                updated_at=now,
                finished_at=None,
            )
        ),
    )
    if requeued.rowcount:
        logger.warning(
            "Requeued %d interrupted route generation job(s) as Pending after restart.",
            requeued.rowcount,
        )

    failed = cast(
        "CursorResult[Any]",
        await session.execute(
            update(Job)
            .where(col(Job.progress) == ProgressEnum.RUNNING)
            .where(col(Job.route_group_id).is_(None))
            .where(col(Job.retry_count) >= MAX_AUTO_REQUEUE_ATTEMPTS)
            .values(
                progress=ProgressEnum.FAILED,
                error_message=RECOVERY_ERROR_MESSAGE,
                updated_at=now,
                finished_at=now,
            )
        ),
    )
    if failed.rowcount:
        logger.warning(
            "Marked %d interrupted route generation job(s) as Failed after "
            "restart (automatic retry already used).",
            failed.rowcount,
        )

    await session.commit()

    pending = (
        await session.execute(
            select(Job.job_id).where(col(Job.progress) == ProgressEnum.PENDING).limit(1)
        )
    ).scalar_one_or_none()
    if pending is not None:
        logger.info(
            "Found PENDING route generation job(s) on startup; waking the worker."
        )
        wake_route_generation_worker()


async def route_generation_worker_loop() -> None:
    """Sleep until woken, then drain PENDING jobs one at a time.

    Single-process assumption: ``_claim_and_run_one`` returning False means the
    queue is empty. That is an unsafe assumption if multiple processes claim concurrently.
    """
    logger.info("Route generation worker started")
    try:
        while True:
            await _wake_event.wait()
            _wake_event.clear()
            while True:
                ran = await _claim_and_run_one()
                if not ran:
                    break
    except asyncio.CancelledError:
        logger.info("Route generation worker stopping")
        raise


async def _claim_and_run_one() -> bool:
    """Claim one job and run it. Returns False when claim finds no PENDING job.

    Under a single worker process, that means the queue is empty. With multiple
    processes, ``None`` can also mean another process claimed first.
    """
    session_maker = app_models.async_session_maker_instance
    if session_maker is None:
        logger.error(
            "Cannot run route generation: database session maker is not initialized."
        )
        return False

    algorithm = get_routing_algorithm()
    async with session_maker() as session:
        job_id = await claim_next_pending_job(session)
        if job_id is None:
            return False
        logger.info("Claimed route generation job %s", job_id)
        started = time.perf_counter()
        await run_generation_job(job_id, session, algorithm)
        logger.info(
            "Finished route generation job %s in %.1fs",
            job_id,
            time.perf_counter() - started,
        )
        return True


def start_route_generation_worker() -> asyncio.Task[None]:
    """Start the background worker task. Call once from app lifespan."""
    global _worker_task
    if _worker_task is not None and not _worker_task.done():
        return _worker_task

    _wake_event.clear()
    _worker_task = asyncio.create_task(
        route_generation_worker_loop(),
        name="route_generation_worker",
    )
    return _worker_task


async def stop_route_generation_worker() -> None:
    """Cancel the background worker task. Call once from app lifespan shutdown."""
    global _worker_task
    if _worker_task is None:
        return

    _worker_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await _worker_task
    _worker_task = None

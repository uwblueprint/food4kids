import logging
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.enum import ProgressEnum
from app.models.job import Job
from app.schemas.route_generation import RouteGenerationGroupInput


class JobService:
    """Service for managing route generation jobs and their progress"""

    def __init__(self, logger: logging.Logger, session: AsyncSession):
        self.logger = logger
        self.session = session

    async def get_jobs(self, progress: ProgressEnum | None = None) -> list[Job]:
        """Get all jobs - optionally filtered by progress."""
        statement = select(Job)
        if progress:
            statement = statement.where(Job.progress == progress)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    def est_now_naive(self) -> datetime:
        return datetime.now(ZoneInfo("America/New_York")).replace(tzinfo=None)

    async def generate_job(self, _req: RouteGenerationGroupInput | None = None) -> UUID:
        """Create a job"""
        try:
            job = Job(progress=ProgressEnum.PENDING)
            self.session.add(job)
            await self.session.commit()
            await self.session.refresh(job)
            return job.job_id
        except Exception as error:
            self.logger.error("Error creating job")
            await self.session.rollback()
            raise error

    async def get_job(self, job_id: UUID) -> Job | None:
        """Get a job by job ID"""
        result = await self.session.execute(select(Job).where(Job.job_id == job_id))
        return result.scalar_one_or_none()

    async def update_progress(self, job_id: UUID, progress: ProgressEnum) -> None:
        try:
            job = await self.get_job(job_id)
            if not job:
                self.logger.error("No job with corresponding job ID")
                return
            if job.progress == ProgressEnum.CANCELLED:
                self.logger.info(
                    "Ignoring progress update for cancelled job %s: requested %s",
                    job_id,
                    progress,
                )
                return
            job.progress = progress
            job.updated_at = self.est_now_naive()
            if progress in (
                ProgressEnum.CANCELLED,
                ProgressEnum.COMPLETED,
                ProgressEnum.FAILED,
            ):
                job.finished_at = self.est_now_naive()
            self.session.add(job)
            await self.session.commit()
        except Exception as error:
            self.logger.error("Error creating job")
            await self.session.rollback()
            raise error

    async def cancel_job(self, job_id: UUID) -> Job | None:
        """Cancel pending/running route generation work.

        Completed, failed, and already-cancelled jobs are treated as safe
        no-ops and returned unchanged.
        """
        try:
            job = await self.get_job(job_id)
            if not job:
                self.logger.error("Job %s not found during cancellation", job_id)
                return None

            if job.progress in (
                ProgressEnum.COMPLETED,
                ProgressEnum.FAILED,
                ProgressEnum.CANCELLED,
            ):
                return job

            now = self.est_now_naive()
            job.progress = ProgressEnum.CANCELLED
            job.updated_at = now
            job.finished_at = now
            self.session.add(job)
            await self.session.commit()
            await self.session.refresh(job)
            return job
        except Exception as error:
            self.logger.error("Error cancelling job")
            await self.session.rollback()
            raise error

    async def enqueue(self, job_id: UUID) -> None:
        try:
            job = await self.get_job(job_id)

            if not job:
                self.logger.error("Job %s not found during enqueue", job_id)
                return

            if job.progress != ProgressEnum.PENDING:
                self.logger.warning(
                    "Cannot enqueue job %s: current state is %s, expected PENDING",
                    job_id,
                    job.progress,
                )
                return

            job.progress = ProgressEnum.RUNNING
            job.started_at = self.est_now_naive()
            self.session.add(job)
            await self.session.commit()
        except Exception:
            self.logger.exception("Enqueue failed for job %s", job_id)
            try:
                await self.update_progress(job_id, ProgressEnum.FAILED)
            except Exception:
                self.logger.exception("Failed to mark job %s as FAILED", job_id)

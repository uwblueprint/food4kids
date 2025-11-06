import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.enum import ProgressEnum
from app.models.job import Job
from app.schemas.route_generation import RouteGenerationGroupInput


class JobService:
    """Modern FastAPI-style job service"""

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

    def utc_now_naive(self) -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)

    async def generate_job(self, _req: RouteGenerationGroupInput | None = None) -> UUID:
        """Create a job"""
        try:
            job = Job(progress=ProgressEnum.PENDING)
            self.session.add(job)
            await self.session.commit()
            await self.session.refresh(job)
            return job.job_id
        except IntegrityError:
            self.logger.exception("Integrity error creating job")
            await self.session.rollback()
        except SQLAlchemyError:
            self.logger.exception("Error in creating job")
            await self.session.rollback()

    async def get_job(self, job_id: UUID) -> Job | None:
        """Get a job by job ID"""
        result = await self.session.execute(select(Job).where(Job.job_id == job_id))
        return result.scalar_one_or_none()

    async def update_progress(self, job_id: UUID, progress: ProgressEnum):
        try:
            job = await self.get_job(job_id)
            if not job:
                return
            job.progress = progress
            job.updated_at = self.utc_now_naive()
            if progress in (ProgressEnum.COMPLETED, ProgressEnum.FAILED):
                job.finished_at = self.utc_now_naive()
            self.session.add(job)
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            self.logger.exception("DB error updating progress for job %s", job_id)
            raise

    async def enqueue(self, job_id: UUID) -> None:
        try:
            job = await self.get_job(job_id)
            if not job:
                self.logger.error("Job %s not found during enqueue", job_id)
                return

            job.started_at = self.utc_now_naive()
            self.session.add(job)
            await self.session.commit()
        except Exception:
            self.logger.exception("Enqueue failed for job %s", job_id)
            try:
                await self.update_progress(job_id, ProgressEnum.FAILED)
            except Exception:
                self.logger.exception("Failed to mark job %s as FAILED", job_id)

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.enum import ProgressEnum
from app.models.generation_types import RouteGenerationRequest
from app.models.job import Job


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

    async def create_generation_job(self, req: RouteGenerationRequest) -> Job:
        """Create a job"""
        job = Job(progress=ProgressEnum.PENDING, payload=req.model_dump())
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_job(self, job_id: UUID) -> Job | None:
        """Get a job by job ID"""
        result = await self.session.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def enqueue(self, job_id: UUID) -> None:
        self.logger.info("Route generation job enqueued", job_id)

        job = await self.get_job(job_id)
        if job:
            job.message = "queued"
            self.session.add(job)
            await self.session.commit()

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

<<<<<<< HEAD
<<<<<<< HEAD
from app.models.enum import ProgressEnum
<<<<<<< HEAD
=======
>>>>>>> 653b6fc (add route to get all routes)
=======
from app.models.enum import ProgressEnum
>>>>>>> 31f7f05 (add copiolet suggestions)
=======
from app.models.generation_type import RouteGenerationRequest
>>>>>>> 8fdc839 (create inital skeleton for generation service)
from app.models.job import Job
from app.services.interfaces.job_service import IJobService


<<<<<<< HEAD
class JobService:
<<<<<<< HEAD
    """Modern FastAPI-style job service"""

=======
>>>>>>> 653b6fc (add route to get all routes)
=======
class JobService(IJobService):
>>>>>>> f642f68 (run formatter)
    def __init__(self, logger: logging.Logger, session: AsyncSession):
        self.logger = logger
        self.session = session

<<<<<<< HEAD
<<<<<<< HEAD
    async def get_jobs(self, progress: ProgressEnum | None = None) -> list[Job]:
        """Get all jobs - optionally filtered by progress."""
=======
    async def get_jobs(self, progress: str | None = None) -> list[Job]:
=======
    async def get_jobs(self, progress: ProgressEnum | None = None) -> list[Job]:
>>>>>>> 31f7f05 (add copiolet suggestions)
        """Get all jobs"""
>>>>>>> 653b6fc (add route to get all routes)
        statement = select(Job)
        if progress:
            statement = statement.where(Job.progress == progress)
        result = await self.session.execute(statement)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        return list(result.scalars().all())
<<<<<<< HEAD
=======
        return result.scalars().all()
>>>>>>> 653b6fc (add route to get all routes)
=======
        return result.scalars().all()
>>>>>>> f642f68 (run formatter)
=======
        return list(result.scalars().all())
>>>>>>> 7c99254 (fix linter errors)
=======

    async def create_generation_job(self, req: RouteGenerationRequest) -> Job:
        job = Job(progress=ProgressEnum.PENDING, payload=req.model_dump())
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_job(self, job_id: UUID) -> Job | None:
        result = await self.session.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()
>>>>>>> 8fdc839 (create inital skeleton for generation service)

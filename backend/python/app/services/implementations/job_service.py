import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

<<<<<<< HEAD
from app.models.enum import ProgressEnum
=======
>>>>>>> 653b6fc (add route to get all routes)
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
    async def get_jobs(self, progress: ProgressEnum | None = None) -> list[Job]:
        """Get all jobs - optionally filtered by progress."""
=======
    async def get_jobs(self, progress: str | None = None) -> list[Job]:
        """Get all jobs"""
>>>>>>> 653b6fc (add route to get all routes)
        statement = select(Job)
        if progress:
            statement = statement.where(Job.progress == progress)
        result = await self.session.execute(statement)
<<<<<<< HEAD
<<<<<<< HEAD
        return list(result.scalars().all())
=======
        return result.scalars().all()
>>>>>>> 653b6fc (add route to get all routes)
=======
        return result.scalars().all()
>>>>>>> f642f68 (run formatter)

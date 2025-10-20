import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

<<<<<<< HEAD
from app.models.enum import ProgressEnum
=======
>>>>>>> 653b6fc (add route to get all routes)
from app.models.job import Job


class JobService:
<<<<<<< HEAD
    """Modern FastAPI-style job service"""

=======
>>>>>>> 653b6fc (add route to get all routes)
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
        return list(result.scalars().all())
=======
        return result.scalars().all()
>>>>>>> 653b6fc (add route to get all routes)

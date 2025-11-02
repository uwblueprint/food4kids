import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.enum import ProgressEnum
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

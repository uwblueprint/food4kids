import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.job import Job


class JobService:
    def __init__(self, logger: logging.Logger, session: AsyncSession):
        self.logger = logger
        self.session = session

    async def get_jobs(self, progress: str | None = None) -> list[Job]:
        """Get all jobs"""
        statement = select(Job)
        if progress:
            statement = statement.where(Job.progress == progress)
        result = await self.session.execute(statement)
        return result.scalars().all()

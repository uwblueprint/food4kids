import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.system_settings import SystemSettings


class SystemSettingsService:
    """Service for reading and writing the singleton SystemSettings row."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_settings(self, session: AsyncSession) -> SystemSettings | None:
        """Return the SystemSettings row, or None if none has been created yet."""
        result = await session.execute(select(SystemSettings))
        return result.scalars().first()

    async def set_import_column_map(
        self, session: AsyncSession, column_map: dict[str, str]
    ) -> None:
        """Persist the import column map, creating the row if it doesn't exist yet.

        Caller is responsible for committing the surrounding transaction.
        """
        settings = await self.get_settings(session)
        if settings is None:
            settings = SystemSettings(import_column_map=column_map)
            session.add(settings)
        else:
            settings.import_column_map = column_map

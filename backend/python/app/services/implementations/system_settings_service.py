import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.system_settings import SystemSettings, SystemSettingsUpdate


class SystemSettingsService:
    """Service for reading and writing the singleton SystemSettings row."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_settings(self, session: AsyncSession) -> SystemSettings | None:
        """Return the SystemSettings row, or None if none has been created yet."""
        result = await session.execute(select(SystemSettings))
        return result.scalars().first()

    async def update_settings(
        self, session: AsyncSession, settings_data: SystemSettingsUpdate
    ) -> SystemSettings:
        """Patch the singleton settings row, creating it if needed."""
        settings = await self.get_settings(session)
        updates = settings_data.model_dump(exclude_unset=True)

        if settings is None:
            settings = SystemSettings(**updates)
            session.add(settings)
            return settings

        for field_name, value in updates.items():
            setattr(settings, field_name, value)
        return settings

    async def set_import_column_map(
        self, session: AsyncSession, column_map: dict[str, str]
    ) -> None:
        """Persist the import column map, creating the row if it doesn't exist yet.

        Caller is responsible for committing the surrounding transaction.
        """
        await self.update_settings(
            session, SystemSettingsUpdate(import_column_map=column_map)
        )

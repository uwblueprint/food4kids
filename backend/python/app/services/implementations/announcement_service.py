import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.models.announcement import (
    Announcement,
    AnnouncementCreate,
    AnnouncementUpdate,
)


class AnnouncementService:
    """Service for managing announcements"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_announcements(self, session: AsyncSession) -> list[Announcement]:
        """Get all announcements; edited posts sort to top via updated_at."""
        statement = (
            select(Announcement)
            .options(selectinload(Announcement.user))  # type: ignore[arg-type]
            .order_by(Announcement.updated_at.desc())  # type: ignore[union-attr]
        )
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_announcement(
        self, session: AsyncSession, announcement_id: UUID
    ) -> Announcement | None:
        """Get announcement by ID"""
        statement = (
            select(Announcement)
            .options(selectinload(Announcement.user))  # type: ignore[arg-type]
            .where(Announcement.announcement_id == announcement_id)
        )
        result = await session.execute(statement)
        announcement = result.scalars().first()

        if not announcement:
            self.logger.error(f"Announcement with id {announcement_id} not found")
            return None

        return announcement

    async def create_announcement(
        self, session: AsyncSession, announcement_data: AnnouncementCreate
    ) -> Announcement:
        """Create new announcement"""
        try:
            announcement = Announcement(**announcement_data.model_dump())

            session.add(announcement)
            await session.commit()
            loaded = await self.get_announcement(session, announcement.announcement_id)
            if loaded is None:
                raise RuntimeError("Created announcement could not be loaded")
            return loaded

        except Exception as error:
            self.logger.error(f"Failed to create announcement: {error!s}")
            await session.rollback()
            raise error

    async def update_announcement(
        self,
        session: AsyncSession,
        announcement_id: UUID,
        announcement_data: AnnouncementUpdate,
    ) -> Announcement | None:
        """Update existing announcement"""
        try:
            announcement = await self.get_announcement(session, announcement_id)

            if not announcement:
                return None

            update_data = announcement_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(announcement, field, value)

            await session.commit()
            return await self.get_announcement(session, announcement_id)

        except Exception as error:
            self.logger.error(f"Failed to update announcement: {error!s}")
            await session.rollback()
            raise error

    async def delete_announcement(
        self, session: AsyncSession, announcement_id: UUID
    ) -> bool:
        """Delete announcement by ID"""
        try:
            statement = select(Announcement).where(
                Announcement.announcement_id == announcement_id
            )
            result = await session.execute(statement)
            announcement = result.scalars().first()

            if not announcement:
                self.logger.error(f"Announcement with id {announcement_id} not found")
                return False

            await session.delete(announcement)
            await session.commit()

            return True

        except Exception as error:
            self.logger.error(f"Failed to delete announcement: {error!s}")
            await session.rollback()
            raise error

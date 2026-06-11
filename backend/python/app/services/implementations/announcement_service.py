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

    def _can_manage(self, announcement: Announcement, user_id: UUID) -> bool:
        if announcement.user_id == user_id:
            return True
        role = announcement.user.role if announcement.user else None
        return role is not None and role.lower() == "admin"

    async def get_announcements(self, session: AsyncSession) -> list[Announcement]:
        """Get all announcements, ordered by most recent first"""
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
        self,
        session: AsyncSession,
        user_id: UUID,
        announcement_data: AnnouncementCreate,
    ) -> Announcement:
        """Create new announcement"""
        try:
            announcement = Announcement(
                user_id=user_id,
                **announcement_data.model_dump(),
            )

            session.add(announcement)
            await session.commit()
            loaded = await self.get_announcement(session, announcement.announcement_id)
            assert loaded is not None
            return loaded

        except Exception as error:
            self.logger.error(f"Failed to create announcement: {error!s}")
            await session.rollback()
            raise error

    async def update_announcement(
        self,
        session: AsyncSession,
        announcement_id: UUID,
        user_id: UUID,
        announcement_data: AnnouncementUpdate,
    ) -> Announcement | None:
        """Update existing announcement"""
        try:
            announcement = await self.get_announcement(session, announcement_id)

            if not announcement:
                return None

            if not self._can_manage(announcement, user_id):
                raise PermissionError(
                    "Only the author or an admin can edit this announcement"
                )

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
        self, session: AsyncSession, announcement_id: UUID, user_id: UUID
    ) -> bool:
        """Delete announcement by ID"""
        try:
            announcement = await self.get_announcement(session, announcement_id)

            if not announcement:
                self.logger.error(f"Announcement with id {announcement_id} not found")
                return False

            if not self._can_manage(announcement, user_id):
                raise PermissionError(
                    "Only the author or an admin can delete this announcement"
                )

            await session.delete(announcement)
            await session.commit()

            return True

        except Exception as error:
            self.logger.error(f"Failed to delete announcement: {error!s}")
            await session.rollback()
            raise error

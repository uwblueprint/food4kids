import logging
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from app.models.announcement import (
    Announcement,
    AnnouncementCreate,
    AnnouncementUpdate,
)
from app.models.announcement_last_read import AnnouncementLastRead
from app.models.user import User


class AnnouncementService:
    """Service for managing announcements"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    @staticmethod
    def _est_now_naive() -> datetime:
        return datetime.now(ZoneInfo("America/New_York")).replace(tzinfo=None)

    async def _get_user_role(self, session: AsyncSession, user_id: UUID) -> str | None:
        statement = select(User.role).where(User.user_id == user_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def _can_manage(
        self, session: AsyncSession, announcement: Announcement, user_id: UUID
    ) -> bool:
        if announcement.user_id == user_id:
            return True
        user_role = await self._get_user_role(session, user_id)
        return user_role is not None and user_role.lower() == "admin"

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
            if loaded is None:
                raise RuntimeError(
                    "Announcement was created but could not be loaded from the database"
                )
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

            if not await self._can_manage(session, announcement, user_id):
                raise PermissionError(
                    "Only the author or an admin can edit this announcement"
                )

            update_data = announcement_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(announcement, field, value)

            if update_data:
                announcement.updated_at = self._est_now_naive()

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

            if not await self._can_manage(session, announcement, user_id):
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

    # --- Read Tracking ---

    async def mark_announcements_as_read(
        self, session: AsyncSession, user_id: UUID
    ) -> AnnouncementLastRead:
        """Upsert the user's last_read_at timestamp to now"""
        try:
            # Validate user exists
            user_statement = select(User).where(User.user_id == user_id)
            user_result = await session.execute(user_statement)
            if not user_result.scalars().first():
                raise ValueError(f"User with id {user_id} not found")

            statement = select(AnnouncementLastRead).where(
                AnnouncementLastRead.user_id == user_id
            )
            result = await session.execute(statement)
            entry = result.scalars().first()

            now = datetime.now(ZoneInfo("America/New_York")).replace(tzinfo=None)

            if entry:
                entry.last_read_at = now
                entry.updated_at = now
            else:
                entry = AnnouncementLastRead(user_id=user_id, last_read_at=now)
                session.add(entry)

            await session.commit()
            await session.refresh(entry)
            return entry

        except Exception as error:
            self.logger.error(f"Failed to mark announcements as read: {error!s}")
            await session.rollback()
            raise error

    async def get_last_read_at(
        self, session: AsyncSession, user_id: UUID
    ) -> datetime | None:
        """Get the user's last_read_at timestamp, or None if never read"""
        statement = select(AnnouncementLastRead.last_read_at).where(
            AnnouncementLastRead.user_id == user_id
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()

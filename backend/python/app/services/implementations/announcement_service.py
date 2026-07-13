import logging
from datetime import datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from app.models.announcement import (
    Announcement,
    AnnouncementCreate,
    AnnouncementUpdate,
)
from app.models.announcement_last_read import AnnouncementLastRead
from app.models.driver import Driver
from app.models.user import User
from app.services.implementations.email_dispatcher import EmailDispatcher


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

    async def send_announcement_emails_to_drivers(
        self,
        session: AsyncSession,
        announcement_id: UUID,
        dispatcher: EmailDispatcher,
        frontend_base_url: str,
    ) -> dict[str, int]:
        """Email all active drivers about an announcement."""
        announcement = await self.get_announcement(session, announcement_id)
        if announcement is None:
            raise ValueError(f"Announcement with id {announcement_id} not found")

        statement = (
            select(User)
            .join(Driver, col(Driver.user_id) == col(User.user_id))
            .where(col(Driver.active).is_(True))
        )
        result = await session.execute(statement)
        drivers = list(result.scalars().all())

        announcement_url = f"{frontend_base_url.rstrip('/')}/driver/home"
        sent_count = 0
        failed_count = 0

        for user in drivers:
            context = {
                "Driver_Name_To_Replace": user.full_name,
                "Announcement_Name": announcement.subject,
                "Announcement_Body": announcement.message,
                "Announcement_URL": announcement_url,
            }
            try:
                await dispatcher.dispatch(
                    email_type="check-latest-announcement",
                    to=user.email,
                    context=context,
                )
                sent_count += 1
            except Exception as error:
                failed_count += 1
                self.logger.error(
                    "Failed to send announcement email to %s: %s",
                    user.email,
                    error,
                    exc_info=True,
                )

        return {"sent": sent_count, "failed": failed_count}

    # --- Read Tracking ---

    async def mark_announcements_as_read(
        self, session: AsyncSession, user_id: UUID
    ) -> AnnouncementLastRead:
        """Upsert the user's last_read_at timestamp to now.

        Uses INSERT ... ON CONFLICT so concurrent mark-read requests for the
        same user cannot race into a unique-constraint IntegrityError.
        """
        try:
            # Validate user exists
            user_statement = select(User).where(User.user_id == user_id)
            user_result = await session.execute(user_statement)
            if not user_result.scalars().first():
                raise ValueError(f"User with id {user_id} not found")

            now = datetime.now(ZoneInfo("America/New_York")).replace(tzinfo=None)
            insert_stmt = pg_insert(AnnouncementLastRead).values(
                announcement_last_read_id=uuid4(),
                user_id=user_id,
                last_read_at=now,
                created_at=now,
                updated_at=now,
            )
            upsert_statement = insert_stmt.on_conflict_do_update(
                constraint="uq_announcement_last_reads_user",
                set_={
                    "last_read_at": insert_stmt.excluded.last_read_at,
                    "updated_at": insert_stmt.excluded.updated_at,
                },
            ).returning(AnnouncementLastRead)

            result = await session.execute(upsert_statement)
            entry = result.scalar_one()
            await session.commit()
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

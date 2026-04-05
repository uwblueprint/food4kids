import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.user_invite import UserInvite, UserInviteCreate


class UserInviteService:
    """Modern FastAPI-style user invite service"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_user_invite_by_id(self, session: AsyncSession, user_invite_id: UUID) -> UserInvite | None:
        """Get user invite by ID - returns SQLModel instance or None if no UserInvite exists"""
        statement = select(UserInvite).where(UserInvite.user_invite_id == user_invite_id)
        result = await session.execute(statement)
        user_invite = result.scalars().first()

        return user_invite
        
    async def create_user_invite(
        self,
        session: AsyncSession,
        user_invite_data: UserInviteCreate,
    ) -> UserInvite:
        """Create new user invite"""
        # Create database user invite
        user_invite = UserInvite(
            user_id=user_invite_data.user_id
        )

        session.add(user_invite)
        await session.flush()
        return user_invite

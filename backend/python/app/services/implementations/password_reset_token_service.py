import hashlib
import logging
import secrets
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.password_reset_token import PasswordResetToken, PasswordResetTokenCreate


class PasswordResetTokenService:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def create(self, session: AsyncSession, user_id: UUID) -> str:
        """Generate and store a password reset token, replacing any existing one"""
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        await session.execute(
            delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id)
        )

        new_token = PasswordResetTokenCreate(user_id=user_id, token_hash=token_hash)
        session.add(new_token)
        await session.commit()

        return raw_token

    async def read(self, session: AsyncSession, raw_token: str) -> PasswordResetToken | None:
        """Retrieve a token object by its raw token value"""
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        result = await session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def delete(self, session: AsyncSession, token_obj: PasswordResetToken) -> None:
        """Delete a specific token object"""
        session.delete(token_obj)
        await session.commit()

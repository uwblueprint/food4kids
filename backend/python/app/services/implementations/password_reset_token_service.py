import hashlib
import logging
import secrets
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from app.models.password_reset_token import PasswordResetToken


class PasswordResetTokenService:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def create(self, session: AsyncSession, user_id: UUID) -> str:
        """Generate and store a password reset token, replacing any existing one"""
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        await session.execute(
            delete(PasswordResetToken).where(col(PasswordResetToken.user_id) == user_id)
        )

        new_token = PasswordResetToken(user_id=user_id, token_hash=token_hash)
        session.add(new_token)
        await session.commit()

        return raw_token

    async def read(
        self, session: AsyncSession, raw_token: str
    ) -> PasswordResetToken | None:
        """Retrieve a token object by its raw token value"""
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        result = await session.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.token_hash == token_hash)
            .options(selectinload(PasswordResetToken.user))  # type: ignore[arg-type]
            .with_for_update()  # Locks row to prevent replay attacks
        )
        return result.scalar_one_or_none()

    async def delete(
        self, session: AsyncSession, token_obj: PasswordResetToken
    ) -> None:
        """Delete a specific token object"""
        await session.delete(token_obj)
        await session.commit()

    async def mark_as_used(
        self, session: AsyncSession, token_obj: PasswordResetToken
    ) -> None:
        """Mark a password reset token as consumed"""
        token_obj.is_used = True
        session.add(token_obj)
        await session.commit()

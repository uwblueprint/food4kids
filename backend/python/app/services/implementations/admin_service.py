import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.models.admin import Admin
from app.models.user import User


class AdminService:
    """Service for managing admins with Firebase authentication integration"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_admin_id_by_auth_id(
        self, session: AsyncSession, auth_id: str
    ) -> UUID | None:
        """Get admin_id by auth_id"""
        try:
            statement = (
                select(Admin)
                .options(selectinload(Admin.user))  # type: ignore[arg-type]
                .join(Admin.user)  # type: ignore[arg-type]
                .where(User.auth_id == auth_id)
            )
            result = await session.execute(statement)
            admin = result.scalars().first()

            if not admin:
                self.logger.error(f"Admin with auth_id {auth_id} not found")
                return None

            return admin.admin_id
        except Exception as e:
            self.logger.error(f"Failed to get admin_id by auth_id: {e!s}")
            raise e

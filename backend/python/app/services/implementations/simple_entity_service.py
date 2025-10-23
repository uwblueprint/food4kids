import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.simple_entity import (
    SimpleEntity,
    SimpleEntityCreate,
    SimpleEntityUpdate,
)
from app.services.interfaces.simple_entity_service import ISimpleEntityService


class SimpleEntityService(ISimpleEntityService):
    """Modern FastAPI-style simple entity service"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_simple_entities(self, session: AsyncSession) -> list[SimpleEntity]:
        """Get all simple entities - returns SQLModel instances directly"""
        statement = select(SimpleEntity)
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_simple_entity(
        self, session: AsyncSession, simple_entity_id: int
    ) -> SimpleEntity | None:
        """Get simple entity by ID"""
        statement = select(SimpleEntity).where(SimpleEntity.id == simple_entity_id)
        result = await session.execute(statement)
        simple_entity = result.scalars().first()

        if not simple_entity:
            self.logger.error(f"SimpleEntity with id {simple_entity_id} not found")
            return None

        return simple_entity

    async def create_simple_entity(
        self, session: AsyncSession, simple_entity_data: SimpleEntityCreate
    ) -> SimpleEntity:
        """Create new simple entity"""
        try:
            # Create SQLModel instance from data
            simple_entity = SimpleEntity(**simple_entity_data.model_dump())

            session.add(simple_entity)
            await session.commit()
            await session.refresh(simple_entity)

            return simple_entity

        except Exception as error:
            self.logger.error(f"Failed to create simple entity: {error!s}")
            await session.rollback()
            raise error

    async def update_simple_entity(
        self,
        session: AsyncSession,
        simple_entity_id: int,
        simple_entity_data: SimpleEntityUpdate,
    ) -> SimpleEntity | None:
        """Update existing simple entity"""
        try:
            statement = select(SimpleEntity).where(SimpleEntity.id == simple_entity_id)
            result = await session.execute(statement)
            simple_entity = result.scalars().first()

            if not simple_entity:
                self.logger.error(f"SimpleEntity with id {simple_entity_id} not found")
                return None

            # Update fields
            update_data = simple_entity_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(simple_entity, field, value)

            await session.commit()
            await session.refresh(simple_entity)

            return simple_entity

        except Exception as error:
            self.logger.error(f"Failed to update simple entity: {error!s}")
            await session.rollback()
            raise error

    async def delete_simple_entity(
        self, session: AsyncSession, simple_entity_id: int
    ) -> bool:
        """Delete simple entity by ID"""
        try:
            statement = select(SimpleEntity).where(SimpleEntity.id == simple_entity_id)
            result = await session.execute(statement)
            simple_entity = result.scalars().first()

            if not simple_entity:
                self.logger.error(f"SimpleEntity with id {simple_entity_id} not found")
                return False

            await session.delete(simple_entity)
            await session.commit()

            return True

        except Exception as error:
            self.logger.error(f"Failed to delete simple entity: {error!s}")
            await session.rollback()
            raise error

import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.entity import Entity, EntityCreate, EntityUpdate


class EntityService:
    """Modern FastAPI-style entity service"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_entities(self, session: AsyncSession) -> list[Entity]:
        """Get all entities - returns SQLModel instances directly"""
        statement = select(Entity)
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def get_entity(self, session: AsyncSession, entity_id: int) -> Entity | None:
        """Get entity by ID"""
        statement = select(Entity).where(Entity.id == entity_id)
        result = await session.execute(statement)
        entity = result.scalars().first()

        if not entity:
            self.logger.error(f"Entity with id {entity_id} not found")
            return None

        return entity

    async def create_entity(
        self, session: AsyncSession, entity_data: EntityCreate
    ) -> Entity:
        """Create new entity"""
        try:
            # Create SQLModel instance from data
            entity = Entity(**entity_data.model_dump())

            session.add(entity)
            await session.commit()
            await session.refresh(entity)

            return entity

        except Exception as error:
            self.logger.error(f"Failed to create entity: {error!s}")
            await session.rollback()
            raise error

    async def update_entity(
        self, session: AsyncSession, entity_id: int, entity_data: EntityUpdate
    ) -> Entity | None:
        """Update existing entity"""
        try:
            statement = select(Entity).where(Entity.id == entity_id)
            result = await session.execute(statement)
            entity = result.scalars().first()

            if not entity:
                self.logger.error(f"Entity with id {entity_id} not found")
                return None

            # Update fields
            update_data = entity_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(entity, field, value)

            await session.commit()
            await session.refresh(entity)

            return entity

        except Exception as error:
            self.logger.error(f"Failed to update entity: {error!s}")
            await session.rollback()
            raise error

    async def delete_entity(self, session: AsyncSession, entity_id: int) -> bool:
        """Delete entity by ID"""
        try:
            statement = select(Entity).where(Entity.id == entity_id)
            result = await session.execute(statement)
            entity = result.scalars().first()

            if not entity:
                self.logger.error(f"Entity with id {entity_id} not found")
                return False

            await session.delete(entity)
            await session.commit()

            return True

        except Exception as error:
            self.logger.error(f"Failed to delete entity: {error!s}")
            await session.rollback()
            raise error

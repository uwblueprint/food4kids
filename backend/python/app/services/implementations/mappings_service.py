import logging

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.location_mappings import LocationMapping


class MappingsService:
    """Modern FastAPI-style mappings service"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_mappings(self, session: AsyncSession) -> list[LocationMapping]:
        """Get all mappings - returns SQLModel instances"""
        try:
            statement = select(LocationMapping)
            result = await session.execute(statement)
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get mappings: {e!s}")
            raise e

    async def create_mapping(
        self, session: AsyncSession, mapping_data: LocationMapping
    ) -> LocationMapping:
        """Create a new mapping - returns SQLModel instance"""
        try:
            mapping = LocationMapping(
                school_name=mapping_data.school_name,
                contact_name=mapping_data.contact_name,
                address=mapping_data.address,
                phone_number=mapping_data.phone_number,
                longitude=mapping_data.longitude,
                latitude=mapping_data.latitude,
                halal=mapping_data.halal,
                dietary_restrictions=mapping_data.dietary_restrictions,
                num_children=mapping_data.num_children,
                num_boxes=mapping_data.num_boxes,
                notes=mapping_data.notes,
            )

            session.add(mapping)
            await session.commit()
            await session.refresh(mapping)
            return mapping
        except Exception as e:
            self.logger.error(f"Failed to create mapping: {e!s}")
            await session.rollback()
            raise e

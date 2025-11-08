import logging

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.location_mappings import LocationMapping, LocationMappingPreview
from app.utilities.df_utils import get_dataframe


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
                mapping_name=mapping_data.mapping_name,
                mapping=mapping_data.mapping
            )

            session.add(mapping)
            await session.commit()
            await session.refresh(mapping)

            # TODO: add mapping ID to admin table as FK
            return mapping
        except Exception as e:
            self.logger.error(f"Failed to create mapping: {e!s}")
            await session.rollback()
            raise e

    async def preview_mapping(self, file: UploadFile) -> LocationMappingPreview:
        """Preview a location mapping from an uploaded file"""
        try:
            df = await get_dataframe(file)

            headers = df.columns.tolist()
            return LocationMappingPreview(preview_headers=headers)
        except Exception as e:
            self.logger.error(f"Failed to preview mapping: {e!s}")
            raise e

    async def delete_mappings(self, session: AsyncSession) -> None:
        """Delete all mappings"""
        try:
            statement = select(LocationMapping)
            result = await session.execute(statement)
            mappings = result.scalars().all()

            for mapping in mappings:
                await session.delete(mapping)

            await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to delete mappings: {e!s}")
            await session.rollback()
            raise e

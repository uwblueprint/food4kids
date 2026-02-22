import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.location_mappings import (
    LocationMapping,
    LocationMappingCreate,
    LocationMappingUpdate,
)


class LocationMappingService:
    """Modern FastAPI-style location service"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_location_mapping_by_id(
        self, session: AsyncSession, location_mapping_id: UUID
    ) -> LocationMapping:
        """Get location mapping by ID - returns SQLModel instance"""
        try:
            statement = select(LocationMapping).where(
                LocationMapping.location_mapping_id == location_mapping_id
            )
            result = await session.execute(statement)
            location_mapping = result.scalars().first()

            if not location_mapping:
                raise ValueError(
                    f"Location mapping with id {location_mapping_id} not found"
                )

            return location_mapping
        except Exception as e:
            self.logger.error(f"Failed to get location mapping by id: {e!s}")
            raise e

    async def get_location_mappings(
        self, session: AsyncSession
    ) -> list[LocationMapping]:
        """Get all location mappings - returns SQLModel instances"""
        try:
            statement = select(LocationMapping)
            result = await session.execute(statement)
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get location mappings: {e!s}")
            raise e

    async def create_location_mapping(
        self, session: AsyncSession, location_mapping_data: LocationMappingCreate
    ) -> LocationMapping:
        """Create a new location mapping - returns SQLModel instance"""
        try:
            location_mapping = LocationMapping(
                contact_name=location_mapping_data.contact_name,
                address=location_mapping_data.address,
                location_delivery_group=location_mapping_data.location_delivery_group,
                phone_number=location_mapping_data.phone_number,
                num_boxes=location_mapping_data.num_boxes,
                halal=location_mapping_data.halal,
                dietary_restrictions=location_mapping_data.dietary_restrictions,
            )

            session.add(location_mapping)
            await session.commit()
            await session.refresh(location_mapping)
            return location_mapping
        except Exception as e:
            self.logger.error(f"Failed to create location mapping: {e!s}")
            await session.rollback()
            raise e

    async def update_location_mapping_by_id(
        self,
        session: AsyncSession,
        location_mapping_id: UUID,
        updated_location_mapping_data: LocationMappingUpdate,
    ) -> LocationMapping:
        """Update location mapping by ID"""
        try:
            # Get the existing location by ID
            location_mapping = await self.get_location_mapping_by_id(
                session, location_mapping_id
            )

            # Update existing location with new data
            updated_data = updated_location_mapping_data.model_dump(exclude_unset=True)

            for field, value in updated_data.items():
                setattr(location_mapping, field, value)

            await session.commit()
            await session.refresh(location_mapping)
            return location_mapping

        except Exception as e:
            self.logger.error(f"Failed to update location mapping by id: {e!s}")
            await session.rollback()
            raise e

    async def delete_all_location_mappings(self, session: AsyncSession) -> None:
        """Delete all location mappings"""
        try:
            statement = select(LocationMapping)
            result = await session.execute(statement)
            location_mappings = result.scalars().all()

            # Delete all locations
            for location_mapping in location_mappings:
                await session.delete(location_mapping)

            await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to delete all location mappings: {e!s}")
            await session.rollback()
            raise e

    async def delete_location_mapping_by_id(
        self, session: AsyncSession, location_mapping_id: UUID
    ) -> None:
        """Delete location mapping by ID"""
        try:
            statement = select(LocationMapping).where(
                LocationMapping.location_mapping_id == location_mapping_id
            )
            result = await session.execute(statement)
            location_mapping = result.scalars().first()

            if not location_mapping:
                raise ValueError(
                    f"Location mapping with id {location_mapping_id} not found"
                )

            await session.delete(location_mapping)
            await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to delete location mapping by id: {e!s}")
            await session.rollback()
            raise e

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.location import Location, LocationCreate, LocationUpdate
from app.services.interfaces.location_service import ILocationService


class LocationService(ILocationService):
    """Modern FastAPI-style location service"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_location_by_id(
        self, session: AsyncSession, location_id: UUID
    ) -> Location | None:
        """Get location by ID - returns SQLModel instance"""
        try:
            statement = select(Location).where(Location.location_id == location_id)
            result = await session.execute(statement)
            location = result.scalars().first()

            if not location:
                self.logger.error(f"Location with id {location_id} not found")
                return None

            return location
        except Exception as e:
            self.logger.error(f"Failed to get location by id: {e!s}")
            raise e

    async def get_locations(self, session: AsyncSession) -> list[Location]:
        """Get all locations - returns SQLModel instances"""
        try:
            statement = select(Location)
            result = await session.execute(statement)
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get locations: {e!s}")
            raise e

    async def create_location(
        self, session: AsyncSession, location_data: LocationCreate
    ) -> Location:
        """Create a new location - returns SQLModel instance"""
        try:
            location = Location(
                school_name=location_data.school_name,
                contact_name=location_data.contact_name,
                address=location_data.address,
                phone_number=location_data.phone_number,
                longitude=location_data.longitude,
                latitude=location_data.latitude,
                halal=location_data.halal,
                dietary_restrictions=location_data.dietary_restrictions,
                num_children=location_data.num_children,
                num_boxes=location_data.num_boxes,
                notes=location_data.notes,
            )

            session.add(location)
            await session.commit()
            await session.refresh(location)
            return location
        except Exception as e:
            self.logger.error(f"Failed to create location: {e!s}")
            await session.rollback()
            raise e

    async def update_location_by_id(
        self,
        session: AsyncSession,
        location_id: UUID,
        updated_location_data: LocationUpdate,
    ) -> Location:
        """Update location by ID"""
        try:
            # Get the existing location by ID
            location = await self.get_location_by_id(session, location_id)

            # Update existing location with new data
            updated_data = updated_location_data.model_dump(exclude_unset=True)
            for field, value in updated_data.items():
                setattr(location, field, value)

            await session.commit()
            await session.refresh(location)
            return location

        except Exception as e:
            self.logger.error(f"Failed to update location by id: {e!s}")
            await session.rollback()
            raise e

    async def delete_all_locations(self, session: AsyncSession) -> None:
        """Delete all locations"""
        try:
            statement = select(Location)
            result = await session.execute(statement)
            locations = result.scalars().all()

            for location in locations:
                await session.delete(location)

            await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to delete all locations: {e!s}")
            await session.rollback()
            raise e

    async def delete_location_by_id(
        self, session: AsyncSession, location_id: UUID
    ) -> bool:
        """Delete location by ID"""
        try:
            statement = select(Location).where(Location.location_id == location_id)
            result = await session.execute(statement)
            location = result.scalars().first()

            if not location:
                self.logger.error(f"Location with id {location_id} not found")
                return False

            await session.delete(location)
            await session.commit()
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete location by id: {e!s}")
            raise e

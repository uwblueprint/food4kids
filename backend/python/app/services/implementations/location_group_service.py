import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.location_group import (
    LocationGroup,
    LocationGroupCreate,
    LocationGroupUpdate,
)
from app.models.location import Location


class LocationGroupService:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def create_location_group(
        self,
        session: AsyncSession,
        location_group_data: LocationGroupCreate,
    ) -> LocationGroup:
        """Create a new location group"""
        try:
            data = location_group_data.model_dump()
            location_ids = data.pop("location_ids")

            new_location_group = LocationGroup(**data, num_locations=len(location_ids))
            session.add(new_location_group)
            await session.commit()
            await session.refresh(new_location_group)

            # Update each locations location_group_id foreign key
            for location_id in location_ids:
                statement = select(Location).where(Location.location_id == location_id)
                result = await session.execute(statement)
                location = result.scalars().first()

                if location:
                    location.location_group_id = new_location_group.location_group_id
                else:
                    self.logger.warning(f"Location with id {location_id} not found")

            await session.commit()

            return new_location_group
        except Exception as error:
            self.logger.error(f"Failed to create location group: {error!s}")
            await session.rollback()
            raise error

    async def update_location_group(
        self,
        session: AsyncSession,
        location_group_id: UUID,
        location_group_data: LocationGroupUpdate,
    ) -> LocationGroup | None:
        """Update existing location group"""
        try:
            statement = select(LocationGroup).where(
                LocationGroup.location_group_id == location_group_id
            )
            result = await session.execute(statement)
            location_group = result.scalars().first()

            if not location_group:
                self.logger.error(
                    f"Location group with id {location_group_id} not found"
                )
                return None

            # Update fields
            update_data = location_group_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(location_group, field, value)

            await session.commit()
            await session.refresh(location_group)

            return location_group

        except Exception as error:
            self.logger.error(f"Failed to update location group: {error!s}")
            await session.rollback()
            raise error

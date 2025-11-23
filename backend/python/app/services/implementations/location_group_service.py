import logging
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.models.location import Location
from app.models.location_group import (
    LocationGroup,
    LocationGroupCreate,
    LocationGroupRead,
    LocationGroupUpdate,
)

if TYPE_CHECKING:
    from app.services.implementations.location_service import LocationService


class LocationGroupService:
    def __init__(self, logger: logging.Logger, location_service: "LocationService | None" = None):
        self.logger = logger
        self.location_service = location_service

    async def get_location_groups(self, session: AsyncSession) -> list[LocationGroupRead]:
        """Get all location groups"""
        try:
            statement = select(LocationGroup).options(
                selectinload(LocationGroup.locations)
            )
            result = await session.execute(statement)
            groups = result.scalars().unique().all()

            return [
                LocationGroupRead.model_validate(group)
                for group in groups
            ]
        except Exception as error:
            self.logger.error(f"Failed to get location groups: {error!s}")
            raise error

    async def get_location_group(
        self, session: AsyncSession, location_group_id: UUID
    ) -> LocationGroup | None:
        """Get location group by ID"""
        statement = select(LocationGroup).options(selectinload(LocationGroup.locations)).where(
            LocationGroup.location_group_id == location_group_id
        )
        result = await session.execute(statement)
        location_group = result.scalars().first()

        if not location_group:
            self.logger.error(
                f"Location group with id {location_group_id} not found")
            return None

        return location_group

    async def create_location_group(
        self,
        session: AsyncSession,
        location_group_data: LocationGroupCreate,
    ) -> LocationGroup:
        """Create a new location group"""
        try:
            data = location_group_data.model_dump()
            location_ids = data.pop("location_ids")
            location_group = LocationGroup(
                **data)

            session.add(location_group)
            await session.commit()
            await session.refresh(location_group)

            # Update each location's location_group_id foreign key
            for location_id in location_ids:
                location = await self.location_service.get_location_by_id(session, location_id)

                if location:
                    location.location_group_id = (
                        location_group.location_group_id)
                else:
                    self.logger.warning(
                        f"Location with id {location_id} not found")

            await session.commit()

            # Reload with locations for accurate num_locations
            reloaded_group = await self.get_location_group(
                session, location_group.location_group_id
            )
            if not reloaded_group:
                raise Exception(
                    f"Failed to reload created location group with id {location_group.location_group_id}"
                )
            return reloaded_group

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

    async def delete_location_group(
        self, session: AsyncSession, location_group_id: UUID
    ) -> bool:
        """Delete location group by ID"""
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
                return False

            locations_statement = select(Location).where(
                Location.location_group_id == location_group_id
            )
            locations_result = await session.execute(locations_statement)
            locations = locations_result.scalars().all()

            for location in locations:
                location.location_group_id = None

            await session.delete(location_group)
            await session.commit()

            return True

        except Exception as error:
            self.logger.error(f"Failed to delete location group: {error!s}")
            await session.rollback()
            raise error

    async def delete_all_location_groups(self, session: AsyncSession) -> None:
        """Delete all location groups"""
        try:
            # delete all locations with a location group FK
            locations_statement = select(Location).where(
                Location.location_group_id.is_not(None)
            )
            locations_result = await session.execute(locations_statement)
            locations = locations_result.scalars().all()

            for location in locations:
                location.location_group_id = None

            # delete all location groups
            delete_statement = select(LocationGroup)
            result = await session.execute(delete_statement)
            location_groups = result.scalars().all()

            for location_group in location_groups:
                await session.delete(location_group)

            await session.commit()

        except Exception as error:
            self.logger.error(
                f"Failed to delete all location groups: {error!s}")
            await session.rollback()
            raise error

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.location import Location, LocationRead
from app.models.location_group import (
    LocationGroup,
    LocationGroupCreate,
    LocationGroupRead,
    LocationGroupUpdate,
)


class LocationGroupService:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_location_groups(
        self, session: AsyncSession
    ) -> list[LocationGroupRead]:
        """Get all location groups with their locations"""
        try:
            groups_result = await session.execute(select(LocationGroup))
            location_groups = list(groups_result.scalars().all())

            result = []
            for lg in location_groups:
                # fetch all locations for location group
                locations_result = await session.execute(
                    select(Location).where(
                        Location.location_group_id == lg.location_group_id
                    )
                )
                locations = list(locations_result.scalars().all())

                result.append(
                    LocationGroupRead(
                        location_group_id=lg.location_group_id,
                        name=lg.name,
                        color=lg.color,
                        notes=lg.notes,
                        num_locations=len(locations),
                        locations=[
                            LocationRead.model_validate(loc) for loc in locations
                        ],
                    )
                )

            return result
        except Exception as error:
            self.logger.error(f"Failed to get location groups: {error!s}")
            raise error

    async def get_location_group(
        self, session: AsyncSession, location_group_id: UUID
    ) -> LocationGroup | None:
        """Get location group by ID"""
        statement = select(LocationGroup).where(
            LocationGroup.location_group_id == location_group_id
        )
        result = await session.execute(statement)
        location_group = result.scalars().first()

        if not location_group:
            self.logger.error(f"Location group with id {location_group_id} not found")
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

            new_location_group = LocationGroup(**data)
            session.add(new_location_group)
            await session.commit()
            await session.refresh(new_location_group)

            # Update each location's location_group_id foreign key
            for location_id in location_ids:
                statement = select(Location).where(Location.location_id == location_id)
                result = await session.execute(statement)
                location = result.scalars().first()

                if location:
                    if location.location_group_id is not None:
                        self.logger.warning(
                            f"Location with id {location_id} already has a location group set"
                        )
                        location.location_group_id = (
                            new_location_group.location_group_id
                        )
                else:
                    self.logger.warning(f"Location with id {location_id} not found")

            await session.commit()

            # Reload with locations for accurate num_locations
            reloaded_group = await self.get_location_group(
                session, new_location_group.location_group_id
            )
            if not reloaded_group:
                raise Exception(
                    f"Failed to reload created location group with id {new_location_group.location_group_id}"
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

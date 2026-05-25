import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.models.location import Location
from app.models.location_group import (
    LocationGroup,
    LocationGroupCreate,
    LocationGroupUpdate,
)


class LocationGroupService:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_location_groups(self, session: AsyncSession) -> list[LocationGroup]:
        """Get all location groups"""
        try:
            # Eager-load locations so LocationGroupRead.num_locations can be read
            # without triggering an (illegal) lazy load on the async session.
            statement = select(LocationGroup).options(
                selectinload(LocationGroup.locations)  # type: ignore[arg-type]
            )
            result = await session.execute(statement)
            return list(result.scalars().all())
        except Exception as error:
            self.logger.error(f"Failed to get location groups: {error!s}")
            raise error

    async def get_location_group(
        self, session: AsyncSession, location_group_id: UUID
    ) -> LocationGroup | None:
        """Get location group by ID"""
        # Eager-load locations so LocationGroupRead.num_locations can be read
        # without triggering an (illegal) lazy load on the async session.
        statement = (
            select(LocationGroup)
            .where(LocationGroup.location_group_id == location_group_id)
            .options(selectinload(LocationGroup.locations))  # type: ignore[arg-type]
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
            # flush (not commit) so the group is persistent for the FK updates
            # below while keeping the insert + links in one atomic transaction.
            # The PK is a Python-side uuid4 default, so it's already populated.
            await session.flush()

            # Link the requested locations in a single query rather than one
            # SELECT per id.
            result = await session.execute(
                select(Location).where(
                    Location.location_id.in_(location_ids)  # type: ignore[attr-defined]
                )
            )
            locations = result.scalars().all()
            found_ids = {location.location_id for location in locations}

            for location in locations:
                if location.location_group_id is not None:
                    self.logger.warning(
                        f"Location with id {location.location_id} already has a location group set; reassigning"
                    )
                location.location_group_id = new_location_group.location_group_id

            for missing_id in set(location_ids) - found_ids:
                self.logger.warning(f"Location with id {missing_id} not found")

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

            # Reload with locations eager-loaded so the caller can read
            # LocationGroupRead.num_locations without an async lazy load (500).
            reloaded_group = await self.get_location_group(session, location_group_id)
            if not reloaded_group:
                raise Exception(
                    f"Failed to reload updated location group with id {location_group_id}"
                )
            return reloaded_group

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

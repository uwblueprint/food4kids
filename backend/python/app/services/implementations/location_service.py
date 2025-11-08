import logging
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.location import (
    Location,
    LocationCreate,
    LocationImportError,
    LocationImportResponse,
    LocationRead,
    LocationUpdate,
)
from app.utilities.df_utils import get_dataframe
from app.utilities.google_maps_client import GoogleMapsClient
from app.utilities.utils import get_phone_number


class LocationService:
    """Modern FastAPI-style location service"""

    def __init__(self, logger: logging.Logger, google_maps_client: GoogleMapsClient):
        self.logger = logger
        self.google_maps_client = google_maps_client

    async def get_location_by_id(
        self, session: AsyncSession, location_id: UUID
    ) -> Location:
        """Get location by ID - returns SQLModel instance"""
        try:
            statement = select(Location).where(
                Location.location_id == location_id)
            result = await session.execute(statement)
            location = result.scalars().first()

            if not location:
                raise ValueError(f"Location with id {location_id} not found")

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

    async def import_locations(
        self, session: AsyncSession, file: UploadFile
    ) -> LocationImportResponse:
        """Add locations from Apricot data source (CSV or XLSX)"""
        try:
            df = await get_dataframe(file)

            # parse df for locations
            successful_locations: list[LocationRead] = []
            failed_locations: list[LocationImportError] = []

            for _, row in df.iterrows():
                try:
                    # geocode address
                    address = str(row.get("Address"))
                    geocode_result = await self.google_maps_client.geocode_address(
                        address
                    )

                    if not geocode_result:
                        raise ValueError(
                            f"Geocoding failed for address: {address}")

                    # TODO: create field mapper (another story)
                    location = {
                        "contact_name": row.get("Guardian Name"),
                        "address": geocode_result.formatted_address,
                        "phone_number": get_phone_number(str(row.get("Primary Phone"))),
                        "longitude": geocode_result.longitude,
                        "latitude": geocode_result.latitude,
                        "halal": row.get("Halal?") == "Yes",
                        "dietary_restrictions": row.get("Specific Food Restrictions")
                        or "",
                        "num_boxes": row.get("Number of Boxes", 0),
                    }

                    # create location into db
                    location_obj = LocationCreate(**location)
                    created_location = await self.create_location(session, location_obj)
                    successful_locations.append(
                        LocationRead.model_validate(created_location)
                    )
                except Exception as row_error:
                    failed_locations.append(
                        LocationImportError(
                            address=address, error=str(row_error))
                    )

            return LocationImportResponse(
                total_entries=len(df),
                successful_entries=len(successful_locations),
                failed_entries=len(failed_locations),
                successful_locations=successful_locations,
                failed_locations=failed_locations,
            )

        except Exception as e:
            self.logger.error(f"Failed to import locations: {e!s}")
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

            # Delete all locations
            for location in locations:
                await session.delete(location)

            await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to delete all locations: {e!s}")
            await session.rollback()
            raise e

    async def delete_location_by_id(
        self, session: AsyncSession, location_id: UUID
    ) -> None:
        """Delete location by ID"""
        try:
            statement = select(Location).where(
                Location.location_id == location_id)
            result = await session.execute(statement)
            location = result.scalars().first()

            if not location:
                raise ValueError(f"Location with id {location_id} not found")

            await session.delete(location)
            await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to delete location by id: {e!s}")
            await session.rollback()
            raise e

import logging
from uuid import UUID

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.location import (
    Location,
    LocationCreate,
    LocationImportEntry,
    LocationImportResponse,
    LocationImportRow,
    LocationImportStatus,
    LocationUpdate,
)
from app.services.implementations.location_mapping_service import LocationMappingService
from app.utilities.google_maps_client import GoogleMapsClient
from app.utilities.utils import get_phone_number, validate_phone


class LocationService:
    """Service for managing delivery locations with geocoding support"""

    def __init__(
        self,
        logger: logging.Logger,
        google_maps_client: GoogleMapsClient,
        location_mapping_service: LocationMappingService,
    ):
        self.logger = logger
        self.google_maps_service = google_maps_client
        self.location_mapping_service = location_mapping_service

    async def get_location_by_id(
        self, session: AsyncSession, location_id: UUID
    ) -> Location:
        """Get location by ID - returns SQLModel instance"""
        try:
            statement = select(Location).where(Location.location_id == location_id)
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
            if not location_data.longitude or not location_data.latitude:
                address = location_data.address

                geocode_result = await self.google_maps_service.geocode_address(address)

                if not geocode_result:
                    raise ValueError(f"Geocoding failed for address: {address}")

                location_data.address = geocode_result.formatted_address
                location_data.longitude = geocode_result.longitude
                location_data.latitude = geocode_result.latitude
                location_data.place_id = geocode_result.place_id

            location = Location(
                school_name=location_data.school_name,
                contact_name=location_data.contact_name,
                address=location_data.address,
                phone_number=location_data.phone_number,
                longitude=location_data.longitude,
                latitude=location_data.latitude,
                place_id=location_data.place_id,
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
            statement = select(Location).where(Location.location_id == location_id)
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

    async def validate_locations(self, file: UploadFile) -> LocationImportResponse:
        """Validate location import data (no missing fields or local duplicates)"""
        try:
            df = pd.read_csv(file.file)
            rows = []
            loc_keys = set[tuple[str, str]]()

            for index, row in df.iterrows():
                location = await self._parse_row(row)

                location_row = LocationImportRow(
                    row=index + 1,
                    location=location,
                    status=LocationImportStatus.OK,
                )

                # case 1: missing fields
                if await self._has_missing_fields(location):
                    location_row.status = LocationImportStatus.MISSING_ENTRY
                    rows.append(location_row)
                    continue

                # case 2: detect local duplicates based on duplicate address/phone number
                dup_key = (location.address, location.phone_number)
                if dup_key in loc_keys:
                    location_row.status = LocationImportStatus.DUPLICATE
                    rows.append(location_row)
                    continue

                # case 3: valid non-duplicate location
                loc_keys.add(dup_key)
                rows.append(location_row)

            # return metadata about import result
            return LocationImportResponse(
                rows=rows,
                total_rows=len(rows),
                successful_rows=len(
                    [r for r in rows if r.status == LocationImportStatus.OK]
                ),
                unsuccessful_rows=len(
                    [r for r in rows if r.status != LocationImportStatus.OK]
                ),
            )
        except Exception as e:
            self.logger.error(f"Failed to validate locations: {e!s}")
            raise e

    async def _parse_row(self, row: pd.Series) -> LocationImportEntry:
        """Parse a row into a LocationImportEntry"""
        # TODO: getting location field mapping based on user id

        try:
            location_entry = LocationImportEntry(
                contact_name=row.get("Guardian Name", "None"),
                address=row.get("Address", "None"),
                delivery_group=row.get("Delivery Day", "None"),
                phone_number=str(row.get("Primary Phone", "None")),
                num_boxes=int(row.get("Number of Boxes", "None")),
                dietary_restrictions=row.get("Halal?", "None"),
            )
            return location_entry

        except Exception as e:
            self.logger.error(f"Failed to parse row: {e!s}")
            raise e

    async def _has_missing_fields(self, location_entry: LocationImportEntry) -> bool:
        """Check if a location entry has missing fields"""
        return any(value is None for value in location_entry.model_dump().values())

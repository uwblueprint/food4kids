import logging
from uuid import UUID

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.location import (
    Location,
    LocationCreate,
    LocationEntriesResponse,
    LocationEntry,
    LocationEntryStatus,
    LocationUpdate,
    UploadedLocationBase,
)
from app.models.location_group import LocationGroupCreate
from app.models.location_mappings import RequiredLocationField
from app.services.implementations.location_group_service import LocationGroupService
from app.services.implementations.mappings_service import MappingsService
from app.utilities.google_maps_client import GoogleMapsClient
from app.utilities.import_utils import get_df
from app.utilities.utils import get_phone_number


class LocationService:
    """Modern FastAPI-style location service"""

    def __init__(self, logger: logging.Logger, maps_service: GoogleMapsClient, mapping_service: MappingsService, location_group_service: LocationGroupService) -> None:
        self.logger = logger
        self.maps_service = maps_service
        self.mapping_service = mapping_service
        self.location_group_service = location_group_service

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
            if not location_data.longitude or not location_data.latitude:
                address = location_data.address

                geocode_result = await self.maps_service.geocode_address(address)

                if not geocode_result:
                    raise ValueError(
                        f"Geocoding failed for address: {address}")

                location_data.address = geocode_result.formatted_address
                location_data.longitude = geocode_result.longitude
                location_data.latitude = geocode_result.latitude
                location_data.place_id = geocode_result.place_id

            location = Location(
                school_name=location_data.school_name or None,
                contact_name=location_data.contact_name,
                address=location_data.address,
                place_id=location_data.place_id or None,
                phone_number=location_data.phone_number,
                longitude=location_data.longitude or None,
                latitude=location_data.latitude or None,
                halal=location_data.halal or False,
                dietary_restrictions=location_data.dietary_restrictions or "",
                num_children=location_data.num_children or None,
                num_boxes=location_data.num_boxes,
                notes=location_data.notes or "",
            )

            session.add(location)
            await session.commit()
            await session.refresh(location)
            return location
        except Exception as e:
            self.logger.error(f"Failed to create location: {e!s}")
            await session.rollback()
            raise e

    async def find_duplicate_location(self, session: AsyncSession, place_id: str) -> Location | None:
        """Find duplicate location by place ID"""
        try:
            statement = select(Location).where(
                Location.place_id == place_id)
            result = await session.execute(statement)
            location = result.scalars().first()
            return location
        except Exception as e:
            self.logger.error(f"Failed to find duplicate location: {e!s}")
            raise e

    async def validate_locations(
        self, session: AsyncSession, file: UploadFile
    ) -> LocationEntriesResponse:
        """Add locations from Apricot data source (CSV or XLSX)"""
        try:
            df = await get_df(file)

            mapping = await self._get_location_mapping(session)

            all_locations: list[LocationEntry] = []
            successful_locations: list[LocationEntry] = []
            failed_locations: list[LocationEntry] = []
            seen_entries = set()

            for index, row in df.iterrows():
                # extract location data and missing fields
                location, missing_fields = self._construct_location(
                    mapping, row)

                # missing fields detected
                if missing_fields:
                    location_entry = LocationEntry(
                        location=location,
                        status=LocationEntryStatus.MISSING_FIELD,
                        missing_fields=missing_fields,
                        row=index + 1,
                    )
                    failed_locations.append(location_entry)
                    all_locations.append(location_entry)
                    continue

                # detect local duplicates
                hash_key = f"{location.address}|{location.phone_number}"
                if hash_key in seen_entries:
                    location_entry = LocationEntry(
                        location=location,
                        status=LocationEntryStatus.DUPLICATE_ENTRY,
                        missing_fields=missing_fields,
                        row=index + 1,
                    )
                    failed_locations.append(location_entry)
                    all_locations.append(location_entry)
                    continue
                seen_entries.add(hash_key)

                # successful location entry
                location_entry = LocationEntry(
                    location=location,
                    status=LocationEntryStatus.OK,
                    missing_fields=missing_fields,
                    row=index + 1,
                )
                successful_locations.append(location_entry)
                all_locations.append(location_entry)
        except Exception as e:
            self.logger.error(f"Failed to import locations: {e!s}")
            raise

        return LocationEntriesResponse(
            total_entries=len(all_locations),
            successful_entries=len(successful_locations),
            failed_entries=len(failed_locations),
            entries=all_locations,
        )

    async def update_location_by_id(
        self,
        session: AsyncSession,
        location_id: UUID,
        updated_location_data: LocationUpdate,
    ) -> Location:
        """Update location by ID"""
        try:
            location = await self.get_location_by_id(session, location_id)

            # update existing location with new non-address data
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

    async def _get_location_mapping(self, session: AsyncSession) -> dict[str, str]:
        # TODO: USE ADMIN_ID TO RETRIEVE MAPPING
        mappings = await self.mapping_service.get_mappings(session)
        if not mappings:
            raise ValueError("No mappings found for location import")
        return mappings[0].mapping

    def _construct_location(self, mapping: dict[str, str], row: pd.Series):
        location_data = {}
        missing_fields: list[str] = []

        for field in mapping:
            source_field = mapping[field]
            source_value = "" if pd.isna(
                row.get(source_field)) else str(row.get(source_field))

            # edge case - dietary restrictions can be empty
            if field == RequiredLocationField.DIETARY_RESTRICTIONS:
                location_data[field] = source_value
                continue

            # add missing fields
            if not source_value:
                missing_fields.append(field)
                continue

            # process fields
            elif field == RequiredLocationField.PHONE_NUMBER:
                location_data[field] = get_phone_number(
                    source_value)
            elif field == RequiredLocationField.HALAL:
                location_data[field] = source_value == "Yes"
            else:
                location_data[field] = source_value
        return UploadedLocationBase(**location_data), missing_fields

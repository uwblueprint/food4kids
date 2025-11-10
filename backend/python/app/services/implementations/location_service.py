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
    LocationState,
    LocationUpdate,
)
from app.models.location_mappings import RequiredLocationField
from app.services.implementations.mappings_service import MappingsService
from app.utilities.google_maps_client import GoogleMapsClient
from app.utilities.import_utils import MAX_CSV_ROWS, get_df
from app.utilities.utils import get_phone_number


class LocationService:
    """Modern FastAPI-style location service"""

    def __init__(self, logger: logging.Logger, maps_service: GoogleMapsClient, mapping_service: MappingsService):
        self.logger = logger
        self.maps_service = maps_service
        self.mapping_service = mapping_service

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
                place_id=location_data.place_id,
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

    async def import_locations(
        self, session: AsyncSession, file: UploadFile
    ) -> LocationEntriesResponse:
        """Add locations from Apricot data source (CSV or XLSX)"""
        try:
            df = await get_df(file)

            if len(df) > MAX_CSV_ROWS:
                raise ValueError(
                    f"Import file has too many rows ({len(df)}). Maximum allowed is {MAX_CSV_ROWS}."
                )

            # TODO: use admin id to get mapping
            mappings = await self.mapping_service.get_mappings(session)
            mapping = mappings[0].mapping

            all_locations: list[LocationEntry] = []
            successful_locations: list[LocationEntry] = []
            failed_locations: list[LocationEntry] = []

            # parse df for location data
            for index, row in df.iterrows():
                try:
                    location_data = {}
                    for field in mapping:
                        source_field = mapping[field]
                        source_value = "" if pd.isna(
                            row.get(source_field)) else str(row.get(source_field))

                        # edge case - dietary restrictions can be empty
                        if field == RequiredLocationField.DIETARY_RESTRICTIONS:
                            location_data[field] = source_value
                            continue

                        # remaining fields are required
                        if not source_value:
                            raise TypeError(
                                f"Missing required field: {source_field} in row {index + 1}"
                            )
                        elif field == RequiredLocationField.PHONE_NUMBER:
                            location_data[field] = get_phone_number(
                                source_value)
                        elif field == RequiredLocationField.HALAL:
                            location_data[field] = source_value == "Yes"
                        else:
                            location_data[field] = source_value

                    # TODO: create relationship between delivery group and location

                    # handle address geocoding
                    address = location_data.get(RequiredLocationField.ADDRESS)
                    geocode_result = await self.maps_service.geocode_address(address)

                    if not geocode_result:
                        raise ValueError(
                            f"Geocoding failed for address: {address}")

                    # check if location already exists
                    duplicate_location = await self.find_duplicate_location(
                        session, geocode_result.place_id)
                    if duplicate_location:
                        # TODO: need to check for other field changes?
                        location_entry = LocationEntry(
                            location=duplicate_location,
                            status=LocationEntryStatus.DUPLICATE_ENTRY,
                            row=index + 1,
                            delivery_group=location_data.get(
                                RequiredLocationField.DELIVERY_GROUP)
                        )
                        failed_locations.append(location_entry)
                        all_locations.append(location_entry)
                        continue

                    location_data[RequiredLocationField.ADDRESS] = geocode_result.formatted_address
                    location_data["longitude"] = geocode_result.longitude
                    location_data["latitude"] = geocode_result.latitude
                    location_data["place_id"] = geocode_result.place_id
                    delivery_group = location_data.get(
                        RequiredLocationField.DELIVERY_GROUP)

                    # save location into db
                    location = LocationCreate(**location_data)
                    created_location = await self.create_location(session, location)
                    location_entry = LocationEntry(
                        location=created_location,
                        status=LocationEntryStatus.OK,
                        row=index + 1,
                        delivery_group=delivery_group
                    )
                    successful_locations.append(location_entry)
                except TypeError as te:
                    location_entry = LocationEntry(
                        location=None,
                        status=LocationEntryStatus.MISSING_FIELD,
                        row=index + 1,
                        delivery_group=delivery_group,
                        error_message=str(te)
                    )
                    failed_locations.append(location_entry)
                except ValueError as ve:
                    location_entry = LocationEntry(
                        location=None,
                        status=LocationEntryStatus.UNKNOWN_ERROR,
                        row=index + 1,
                        delivery_group=delivery_group,
                        error_message=str(ve)
                    )
                    failed_locations.append(location_entry)
                all_locations.append(location_entry)
            return LocationEntriesResponse(
                total_entries=len(df),
                successful_entries=len(successful_locations),
                failed_entries=len(failed_locations),
                entries=all_locations
            )

        except Exception as e:
            self.logger.error(f"Failed to import locations: {e!s}")
            raise

    async def update_location_by_id(
        self,
        session: AsyncSession,
        location_id: UUID,
        updated_location_data: LocationUpdate,
    ) -> Location:
        """Update location by ID"""
        try:
            location = await self.get_location_by_id(session, location_id)

            # check for address change to create new location entry instead
            if updated_location_data.address:
                geocode_result = await self.maps_service.geocode_address(
                    updated_location_data.address)

                override_location_data = {
                    "address": geocode_result.formatted_address,
                    "longitude": geocode_result.longitude,
                    "latitude": geocode_result.latitude,
                    "place_id": geocode_result.place_id
                }

                # Create new location with updated geocoding, exclude database-only fields
                new_location = LocationCreate(
                    **location.model_dump(exclude=set(override_location_data.keys())),
                    **override_location_data
                )
                created_location = await self.create_location(session, new_location)

                # set old location to inactive
                location.state = LocationState.ARCHIVED
                await session.commit()
                await session.refresh(location)
                return created_location

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

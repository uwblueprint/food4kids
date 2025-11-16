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
    LocationRead,
    LocationUpdate,
)
from app.models.location_group import LocationGroupCreate
from app.models.location_mappings import RequiredLocationField
from app.services.implementations.location_group_service import LocationGroupService
from app.services.implementations.mappings_service import MappingsService
from app.utilities.google_maps_client import GoogleMapsClient
from app.utilities.import_utils import MAX_CSV_ROWS, get_df
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
            if not mappings:
                raise ValueError("No mappings found for location import")
            mapping = mappings[0].mapping

            all_locations: list[LocationEntry] = []
            successful_locations: list[LocationEntry] = []
            failed_locations: list[LocationEntry] = []

            grouped_df = df.groupby(mapping[RequiredLocationField.DELIVERY_GROUP]).apply(
                lambda row: row.to_dict(orient="records"))

            for delivery_group, group_rows in grouped_df.items():
                # parse df for location data

                grouped_locations: list[LocationEntry] = []
                for index, row in enumerate(group_rows):
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

                        # handle address geocoding
                        address = location_data.get(
                            RequiredLocationField.ADDRESS)
                        geocode_result = await self.maps_service.geocode_address(address)

                        if not geocode_result:
                            raise ValueError(
                                f"Geocoding failed for address: {address}")

                        location_data[RequiredLocationField.ADDRESS] = geocode_result.formatted_address
                        location_data["longitude"] = geocode_result.longitude
                        location_data["latitude"] = geocode_result.latitude
                        location_data["place_id"] = geocode_result.place_id

                        # create location into db
                        location = LocationCreate(**location_data)
                        created_location = await self.create_location(session=session, location_data=location)

                        location_entry = LocationEntry(
                            location=created_location,
                            status=LocationEntryStatus.OK,
                            row=index + 1,
                            delivery_group=delivery_group
                        )

                        grouped_locations.append(location_entry)
                    except TypeError as te:
                        location_entry = LocationEntry(
                            location=None,
                            status=LocationEntryStatus.MISSING_FIELD,
                            row=index + 1,
                            delivery_group=delivery_group,
                            error_message=str(te)
                        )
                        failed_locations.append(location_entry)
                        all_locations.append(location_entry)
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

                # create location group for batch
                if grouped_locations:
                    location_group = await self.location_group_service.create_location_group(
                        session=session,
                        location_group_data=LocationGroupCreate(
                            name=delivery_group,
                            color="TODO",
                            location_ids=[
                                location_entry.location.location_id for location_entry in grouped_locations],
                            notes=delivery_group)
                    )

                    # update location entries with location group id
                    for location_entry in grouped_locations:
                        updated_location = await self.update_location_by_id(
                            session=session,
                            location_id=location_entry.location.location_id,
                            updated_location_data=LocationUpdate(
                                location_group_id=location_group.location_group_id
                            )
                        )
                        location_entry.location = updated_location
                        successful_locations.append(location_entry)
                        all_locations.append(location_entry)

            return LocationEntriesResponse(
                total_entries=len(all_locations),
                successful_entries=len(successful_locations),
                failed_entries=len(failed_locations),
                entries=all_locations,
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

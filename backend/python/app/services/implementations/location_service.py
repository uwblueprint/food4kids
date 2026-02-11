import logging
from uuid import UUID

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.location import (
    ImportStatus,
    Location,
    LocationCreate,
    LocationDeduplicationResponse,
    LocationEntry,
    LocationImportEntry,
    LocationImportResponse,
    LocationImportRow,
    LocationImportStatus,
    LocationRead,
    LocationUpdate,
)
from app.services.implementations.location_mapping_service import LocationMappingService
from app.utilities.google_maps_client import GoogleMapsClient
from app.utilities.utils import get_phone_number

# Default CSV column names when no LocationMapping is configured
DEFAULT_COLUMN_MAP = {
    "contact_name": "Guardian Name",
    "address": "Address",
    "delivery_group": "Delivery Day",
    "phone_number": "Primary Phone",
    "num_boxes": "Number of Boxes",
    "halal": "Halal?",
    "dietary_restrictions": "Specific Food Restrictions",
}


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

    async def validate_locations(
        self, session: AsyncSession, file: UploadFile
    ) -> LocationImportResponse:
        """Validate location import data (no missing fields or local duplicates)"""
        try:
            # resolve CSV column mapping from DB, fall back to defaults
            column_map = await self._get_column_map(session)

            df = pd.read_csv(file.file)
            rows: list[LocationImportRow] = []
            loc_keys: set[tuple[str, str]] = set()

            for index, row in df.iterrows():
                location = self._parse_row(row, column_map)

                location_row = LocationImportRow(
                    row=index + 1,
                    location=location,
                    status=LocationImportStatus.OK,
                )

                # case 1: missing required fields
                if self._has_missing_fields(location):
                    location_row.status = LocationImportStatus.MISSING_ENTRY
                    rows.append(location_row)
                    continue

                # case 2: invalid phone number format
                try:
                    location.phone_number = get_phone_number(location.phone_number)
                except (ValueError, Exception):
                    location_row.status = LocationImportStatus.INVALID_FORMAT
                    rows.append(location_row)
                    continue

                # case 3: detect local duplicates based on (address, phone_number)
                dup_key = (location.address, location.phone_number)
                if dup_key in loc_keys:
                    location_row.status = LocationImportStatus.DUPLICATE
                    rows.append(location_row)
                    continue

                # case 4: valid non-duplicate location
                loc_keys.add(dup_key)
                rows.append(location_row)

            successful_rows = len(
                [r for r in rows if r.status == LocationImportStatus.OK]
            )
            status = (
                ImportStatus.SUCCESS
                if successful_rows == len(rows)
                else ImportStatus.FAILURE
            )

            return LocationImportResponse(
                status=status,
                rows=rows,
                total_rows=len(rows),
                successful_rows=successful_rows,
                unsuccessful_rows=len(rows) - successful_rows,
            )
        except Exception as e:
            self.logger.error(f"Failed to validate locations: {e!s}")
            raise e

    async def deduplicate_locations(
        self, session: AsyncSession, rows: list[LocationImportRow]
    ) -> LocationDeduplicationResponse:
        """Deduplicate import rows against existing DB locations."""
        try:
            db_locations = await self.get_locations(session)

            # Build lookup: list of (db_location, normalized_address, phone)
            db_lookup: list[tuple[Location, str, str | None]] = []
            for db_loc in db_locations:
                db_lookup.append(
                    (
                        db_loc,
                        db_loc.address,
                        db_loc.phone_number,
                    )
                )

            net_new: list[LocationEntry] = []
            similar: list[LocationEntry] = []
            duplicate: list[LocationEntry] = []
            matched_db_ids: set = set()

            for row in rows:
                import_addr = row.location.address
                import_phone = row.location.phone_number

                dup_matches: list[LocationRead] = []
                sim_matches: list[LocationRead] = []

                for db_loc, db_addr, db_phone in db_lookup:
                    addr_match = import_addr == db_addr
                    phone_match = import_phone == db_phone

                    if addr_match and phone_match:  # duplicate match
                        db_read = LocationRead.model_validate(db_loc)
                        dup_matches.append(db_read)
                        matched_db_ids.add(db_loc.location_id)
                    elif addr_match or phone_match:  # similar match
                        db_read = LocationRead.model_validate(db_loc)
                        sim_matches.append(db_read)
                        matched_db_ids.add(db_loc.location_id)

                if dup_matches:  # case 1: duplicate match
                    duplicate.append(
                        LocationEntry(location=row, matched_location=dup_matches)
                    )
                if sim_matches:  # case 2: similar match
                    similar.append(
                        LocationEntry(location=row, matched_location=sim_matches)
                    )
                if not dup_matches and not sim_matches:  # case 3: net new entry
                    net_new.append(LocationEntry(location=row))

            stale = [  # case 4: stale entries
                LocationRead.model_validate(db_loc)
                for db_loc in db_locations
                if db_loc.location_id not in matched_db_ids
            ]

            return LocationDeduplicationResponse(
                net_new=net_new,
                similar=similar,
                duplicate=duplicate,
                stale=stale,
            )
        except Exception as e:
            self.logger.error(f"Failed to classify locations: {e!s}")
            raise e

    async def _get_column_map(self, session: AsyncSession) -> dict[str, str]:
        """Get CSV column name mapping from the LocationMapping table, or use defaults."""
        try:
            mappings = await self.location_mapping_service.get_location_mappings(
                session
            )
            if not mappings:
                return DEFAULT_COLUMN_MAP

            # TODO: fetch mapping for user
            mapping = mappings[0]
            return {
                "contact_name": mapping.contact_name,
                "address": mapping.address,
                "delivery_group": mapping.location_delivery_group,
                "phone_number": mapping.phone_number,
                "num_boxes": mapping.num_boxes,
                "halal": mapping.halal,
                "dietary_restrictions": mapping.dietary_restrictions,
            }
        except Exception as e:
            self.logger.warning(f"Failed to load column mapping, using defaults: {e!s}")
            return DEFAULT_COLUMN_MAP

    def _parse_row(
        self, row: pd.Series, column_map: dict[str, str]
    ) -> LocationImportEntry:
        """Parse a CSV row into a LocationImportEntry using the column mapping."""

        def get_value(field: str) -> str | None:
            csv_col = column_map.get(field, "")
            if not csv_col:
                return None
            val = row.get(csv_col)
            if pd.isna(val):
                return None
            return str(val).strip() or None

        def parse_bool(field: str) -> bool | None:
            val = get_value(field)
            if not val:
                return None
            return val.lower() in ("yes", "y")

        def parse_int(field: str) -> int | None:
            val = get_value(field)
            if not val:
                return None
            try:
                return int(float(val))
            except (ValueError, TypeError):
                return None

        return LocationImportEntry(
            contact_name=get_value("contact_name"),
            address=get_value("address"),
            delivery_group=get_value("delivery_group"),
            phone_number=get_value("phone_number"),
            num_boxes=parse_int("num_boxes"),
            halal=parse_bool("halal"),
            dietary_restrictions=get_value("dietary_restrictions"),
        )

    def _has_missing_fields(self, entry: LocationImportEntry) -> bool:
        """Check if any required fields are missing."""
        required = [
            entry.contact_name,
            entry.address,
            entry.delivery_group,
            entry.phone_number,
            entry.num_boxes,
        ]
        return any(not val for val in required)

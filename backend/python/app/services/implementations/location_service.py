import logging
import os
from io import BytesIO
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
    LocationRowStatus,
    LocationState,
    LocationUpdate,
)
from app.utilities.google_maps_client import GoogleMapsClient
from app.utilities.utils import validate_phone

# Allowed file extensions for location import files
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}

# Default CSV column names
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
    ):
        self.logger = logger
        self.google_maps_service = google_maps_client

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
        """Get all active locations - returns SQLModel instances"""
        try:
            statement = select(Location).where(Location.state == LocationState.ACTIVE)
            result = await session.execute(statement)
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get locations: {e!s}")
            raise e

    async def create_location(
        self, session: AsyncSession, location_data: LocationCreate
    ) -> Location:
        """Create a new location using a LocationCreate object - returns SQLModel instance"""
        try:
            location = await self._build_location(location_data)
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
        self, _: AsyncSession, file: UploadFile
    ) -> LocationImportResponse:
        """Validate location import data (no missing fields or local duplicates)"""
        try:
            df = self._read_upload_file(file)
            rows: list[LocationImportRow] = []
            loc_keys: set[tuple[str, str]] = set()

            for index, row in df.iterrows():
                location = self._parse_row(row, DEFAULT_COLUMN_MAP)

                location_row = LocationImportRow(
                    row=index + 1,
                    location=location,
                    status=LocationRowStatus.OK,
                )

                # case 1: missing required fields
                if self._has_missing_fields(location):
                    location_row.status = LocationRowStatus.MISSING_FIELDS
                    rows.append(location_row)
                    continue

                # case 2: invalid phone number format
                try:
                    location.phone_number = validate_phone(location.phone_number)
                except (ValueError, Exception):
                    location_row.status = LocationRowStatus.INVALID_FORMAT
                    rows.append(location_row)
                    continue

                # case 3: detect local duplicates based on (address, phone_number)
                dup_key = (location.address, location.phone_number)
                if dup_key in loc_keys:
                    location_row.status = LocationRowStatus.DUPLICATE
                    rows.append(location_row)
                    continue

                # case 4: valid non-duplicate location
                loc_keys.add(dup_key)
                rows.append(location_row)

            successful_rows = [r for r in rows if r.status == LocationRowStatus.OK]

            return LocationImportResponse(
                status=LocationImportStatus.SUCCESS
                if len(successful_rows) == len(rows)
                else LocationImportStatus.FAILURE,
                rows=rows,
                total_rows=len(rows),
                successful_rows=len(successful_rows),
                unsuccessful_rows=len(rows) - len(successful_rows),
            )
        except Exception as e:
            self.logger.error(f"Failed to validate locations: {e!s}")
            raise e

    def _read_upload_file(self, file: UploadFile) -> pd.DataFrame:
        """Validate file type and read into a DataFrame."""

        filename = file.filename or ""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type '{ext}'. Must be one of: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        # return dataframe using appropriate reader based on file extension
        if ext == ".xlsx":
            return pd.read_excel(
                BytesIO(file.file.read()),
                engine="openpyxl",
                dtype=str,
            )
        return pd.read_csv(
            BytesIO(file.file.read()),
            dtype=str,
        )

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
            return str(val).strip()

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
        required_fields = [
            entry.contact_name,
            entry.address,
            entry.delivery_group,
            entry.phone_number,
            entry.num_boxes,
        ]
        return any(not val for val in required_fields)

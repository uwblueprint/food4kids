import asyncio
import logging
import os
from io import BytesIO
from typing import TypeGuard
from uuid import UUID

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.enum import NotePermission
from app.models.location import (
    AlertCode,
    AlertType,
    Location,
    LocationCreate,
    LocationImportAlert,
    LocationImportEntry,
    LocationImportResponse,
    LocationImportRow,
    LocationImportStatus,
    LocationIngestRequest,
    LocationIngestResponse,
    LocationRead,
    LocationState,
    LocationUpdate,
    ValidatedLocationImportEntry,
)
from app.models.location_group import LocationGroup
from app.models.note_chain import NoteChain
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.utilities.google_maps_client import GoogleMapsClient
from app.utilities.pagination import paginate_query
from app.utilities.utils import validate_phone

# Allowed file extensions for location import files
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

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

    async def get_locations(
        self, session: AsyncSession, pagination: PaginationParams
    ) -> PaginatedResponse[Location]:
        """Get paginated locations - returns PaginatedResponse of SQLModel instances"""
        try:
            statement = (
                select(Location)
                .where(Location.state == LocationState.ACTIVE)
                .order_by(Location.created_at.desc())  # type: ignore[union-attr]
            )
            result, total = await paginate_query(session, statement, pagination)
            items = list(result.scalars().all())
            return PaginatedResponse.create(
                items=items,
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
            )
        except Exception as e:
            self.logger.error(f"Failed to get locations: {e!s}")
            raise e

    async def create_location(
        self, session: AsyncSession, location_data: LocationCreate
    ) -> Location:
        """Create a new location using a LocationCreate object - returns SQLModel instance"""
        try:
            # Auto-create a note chain for the location
            note_chain = NoteChain(
                read_permission=NotePermission.ALL,
                write_permission=NotePermission.ALL,
            )
            session.add(note_chain)
            await session.flush()
            location = await self._build_location(location_data)
            location.note_chain_id = note_chain.note_chain_id
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
        """Validate location import data and return per-row alerts."""
        try:
            df = await self._read_upload_file(file)
            rows: list[LocationImportRow] = []

            # track local duplicates
            full_dup_keys: dict[tuple[str, str, str], int] = {}
            address_keys: dict[str, int] = {}  # track partial duplicates by address
            phone_keys: dict[str, int] = {}  # track partial duplicates by phone

            for index, row in df.iterrows():
                row_num = int(index) + 1  # type: ignore[call-overload]
                location = self._parse_row(row, DEFAULT_COLUMN_MAP)
                alerts: list[LocationImportAlert] = []

                # ERROR: missing required fields — also narrows type to ValidatedLocationImportEntry
                if not self._has_required_fields(location):
                    alerts.append(
                        self._alert(
                            AlertType.ERROR,
                            AlertCode.MISSING_FIELDS,
                            "Missing Field(s)",
                        )
                    )
                    rows.append(
                        LocationImportRow(row=row_num, location=location, alerts=alerts)
                    )
                    continue

                # ERROR: invalid phone number format
                try:
                    location.phone_number = validate_phone(location.phone_number)
                except ValueError:
                    alerts.append(
                        self._alert(
                            AlertType.ERROR,
                            AlertCode.INVALID_FORMAT,
                            "Invalid Phone Number",
                        )
                    )
                    rows.append(
                        LocationImportRow(row=row_num, location=location, alerts=alerts)
                    )
                    continue

                # WARNING: missing delivery group
                if not location.delivery_group:
                    alerts.append(
                        self._alert(
                            AlertType.WARNING,
                            AlertCode.MISSING_DELIVERY_GROUP,
                            "Missing Delivery Group",
                        )
                    )

                # ERROR: full duplicate (same contact name, address, and phone)
                full_key = (
                    location.contact_name,
                    location.address,
                    location.phone_number,
                )

                if full_key in full_dup_keys:
                    alerts.append(
                        self._alert(
                            AlertType.ERROR,
                            AlertCode.LOCAL_DUPLICATE,
                            f"Local Duplicate to Row #{full_dup_keys[full_key]}",
                        )
                    )
                else:
                    full_dup_keys[full_key] = row_num

                    # WARNING: partial duplicate — same address or same phone
                    if location.address in address_keys:
                        alerts.append(
                            self._alert(
                                AlertType.WARNING,
                                AlertCode.PARTIAL_DUPLICATE,
                                f"Address matches Row #{address_keys[location.address]}",
                            )
                        )
                    else:
                        address_keys[location.address] = row_num

                    if location.phone_number in phone_keys:
                        alerts.append(
                            self._alert(
                                AlertType.WARNING,
                                AlertCode.PARTIAL_DUPLICATE,
                                f"Phone matches Row #{phone_keys[location.phone_number]}",
                            )
                        )
                    else:
                        phone_keys[location.phone_number] = row_num

                rows.append(
                    LocationImportRow(row=row_num, location=location, alerts=alerts)
                )

            return LocationImportResponse(
                status=self._get_import_status(rows),
                total_rows=len(rows),
                rows=rows,
            )
        except Exception as e:
            self.logger.error(f"Failed to validate locations: {e!s}")
            raise e

    def _get_import_status(self, rows: list[LocationImportRow]) -> LocationImportStatus:
        """Get the most severe status across all rows."""
        all_alerts = [a for r in rows for a in r.alerts]
        if any(a.type == AlertType.ERROR for a in all_alerts):
            return LocationImportStatus.ERROR
        if any(a.type == AlertType.WARNING for a in all_alerts):
            return LocationImportStatus.WARNING
        return LocationImportStatus.SUCCESS

    async def _read_upload_file(self, file: UploadFile) -> pd.DataFrame:
        """Validate file type and read into a DataFrame."""

        filename = file.filename or ""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type '{ext}'. Must be one of: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        # check file size
        if file.size and file.size > MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds {MAX_FILE_SIZE} bytes")

        # read file into bytes io
        bytes_io = BytesIO(await file.read())
        if ext == ".xlsx":
            return pd.read_excel(
                bytes_io,
                engine="openpyxl",
                dtype=str,
            )
        return pd.read_csv(
            bytes_io,
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

    @staticmethod
    def _has_required_fields(
        entry: LocationImportEntry,
    ) -> TypeGuard[ValidatedLocationImportEntry]:
        """Returns True (and narrows to ValidatedLocationImportEntry) when all required
        fields are present; False when any are missing."""
        return (
            entry.contact_name is not None
            and entry.address is not None
            and entry.phone_number is not None
        )

    async def _build_location(self, location_data: LocationCreate) -> Location:
        """Geocode and build a Location object (does not add to session or commit)."""
        if not location_data.longitude or not location_data.latitude:
            address = location_data.address

            # geocode address to get location metadata
            geocode_result = await self.google_maps_service.geocode_address(address)

            if not geocode_result:
                raise ValueError(f"Geocoding failed for address: {address}")

            location_data.address = geocode_result.formatted_address
            location_data.longitude = geocode_result.longitude
            location_data.latitude = geocode_result.latitude
            location_data.place_id = geocode_result.place_id

        return Location(
            location_group_id=location_data.location_group_id,
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
    

    _GROUP_COLORS = [
        "#EF4444",
        "#F97316",
        "#EAB308",
        "#22C55E",
        "#3B82F6",
        "#A855F7",
        "#EC4899",
    ]

    async def ingest_locations(
        self, session: AsyncSession, request: LocationIngestRequest
    ) -> LocationIngestResponse:
        """Persist net-new locations and archive stale ones."""
        try:
            # Fetch and archive stale locations in one SELECT IN
            stale_ids = [loc.location_id for loc in request.stale]
            stale_db_rows: list[Location] = []
            if stale_ids:
                result = await session.execute(
                    select(Location).where(Location.location_id.in_(stale_ids))
                )
                stale_db_rows = list(result.scalars().all())
                for loc in stale_db_rows:
                    loc.state = LocationState.ARCHIVED

            archived = [LocationRead.model_validate(loc) for loc in stale_db_rows]

            if not request.net_new:
                await session.commit()
                return LocationIngestResponse(created=[], archived=archived)

            # Geocode all addresses concurrently
            geocode_results = await asyncio.gather(
                *[
                    self.google_maps_service.geocode_address(entry.address)
                    for entry in request.net_new
                ]
            )

            # Fetch all existing LocationGroups in one query
            groups_result = await session.execute(select(LocationGroup))
            group_by_name: dict[str, LocationGroup] = {
                g.name: g for g in groups_result.scalars().all()
            }

            # Create missing LocationGroups (batch, deterministic color assignment)
            needed_names = sorted(
                {
                    entry.delivery_group
                    for entry in request.net_new
                    if entry.delivery_group
                    and entry.delivery_group not in group_by_name
                }
            )
            for i, name in enumerate(needed_names):
                color = self._GROUP_COLORS[i % len(self._GROUP_COLORS)]
                group = LocationGroup(name=name, color=color)
                session.add(group)
                group_by_name[name] = group

            # Build and batch-insert new Location records
            new_locations: list[Location] = []
            for entry, geocode_result in zip(request.net_new, geocode_results):
                if not geocode_result:
                    raise ValueError(f"Geocoding failed for address: {entry.address}")

                group = (
                    group_by_name.get(entry.delivery_group)
                    if entry.delivery_group
                    else None
                )
                new_locations.append(
                    Location(
                        contact_name=entry.contact_name,
                        address=geocode_result.formatted_address,
                        phone_number=entry.phone_number,
                        longitude=geocode_result.longitude,
                        latitude=geocode_result.latitude,
                        place_id=geocode_result.place_id,
                        halal=entry.halal or False,
                        dietary_restrictions=entry.dietary_restrictions or "",
                        num_boxes=entry.num_boxes or 0,
                        location_group_id=(group.location_group_id if group else None),
                    )
                )

            session.add_all(new_locations)
            await session.commit()

            for loc in new_locations:
                await session.refresh(loc)

            return LocationIngestResponse(
                created=[LocationRead.model_validate(loc) for loc in new_locations],
                archived=archived,
            )
        except Exception as e:
            self.logger.error(f"Failed to ingest locations: {e!s}")
            await session.rollback()
            raise e

    @staticmethod
    def _alert(type: AlertType, code: AlertCode, message: str) -> LocationImportAlert:
        return LocationImportAlert(type=type, code=code, message=message)

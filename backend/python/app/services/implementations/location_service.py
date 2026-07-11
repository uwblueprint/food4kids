import asyncio
import logging
import os
from collections.abc import Iterable
from datetime import datetime
from io import BytesIO
from typing import TYPE_CHECKING, Any, TypeGuard
from uuid import UUID
from zoneinfo import ZoneInfo

import pandas as pd
from fastapi import UploadFile
from sqlalchemy import and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from app.config import settings
from app.models.enum import (
    LocationStatusEnum,
    NotePermission,
)
from app.models.location import (
    AlertCode,
    Location,
    LocationCreate,
    LocationImportEntry,
    LocationImportResponse,
    LocationImportRow,
    LocationIngestRequest,
    LocationIngestResponse,
    LocationRead,
    LocationUpdate,
    ValidatedLocationImportEntry,
)
from app.models.location_group import LocationGroup
from app.models.note_chain import NoteChain
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_snapshot import RouteSnapshot
from app.models.route_stop import RouteStop
from app.models.route_stop_snapshot import RouteStopSnapshot
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.utilities.google_maps_client import GoogleMapsClient
from app.utilities.pagination import paginate_query
from app.utilities.utils import validate_phone

if TYPE_CHECKING:
    from app.services.implementations.system_settings_service import (
        SystemSettingsService,
    )

# Allowed file extensions for location import files
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Default CSV column names
DEFAULT_COLUMN_MAP = {
    "contact_name": "Guardian Name",
    "address": "Address",
    "delivery_group": "Delivery Day",
    "phone_primary": "Primary Phone",
    "phone_secondary": "Secondary Phone",
    "num_children": "Number of Children",
    "halal": "Halal?",
    "dietary_restrictions": "Specific Food Restrictions",
}


class InvalidDeliveryTypeError(ValueError):
    """Raised when a delivery type is not configured in system settings."""


class LocationInUseError(Exception):
    """Raised when deleting a location that route stops still reference.

    Mapped to 409 by the router — deleting would otherwise fail at the FK
    (route_stops.location_id has no ON DELETE action) with a raw 500."""


class LocationService:
    """Service for managing delivery locations with geocoding support"""

    def __init__(
        self,
        logger: logging.Logger,
        google_maps_client: GoogleMapsClient,
        system_settings_service: "SystemSettingsService",
    ):
        self.logger = logger
        self.google_maps_service = google_maps_client
        self.system_settings_service = system_settings_service
        self.timezone = ZoneInfo(settings.scheduler_timezone)

    def _today_start(self) -> datetime:
        """Midnight at the start of today in the project's configured timezone.

        Naive datetime to match how drive_date is stored (drive_date columns
        are naive — see RouteGroup).
        """
        return datetime.now(self.timezone).replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=None
        )

    async def get_location_by_id(
        self, session: AsyncSession, location_id: UUID
    ) -> Location:
        """Get location by ID - returns SQLModel instance.

        Eager-loads location_group so LocationRead.location_group_name can be
        accessed without an (illegal) async lazy load.
        """
        try:
            statement = (
                select(Location)
                .where(Location.location_id == location_id)
                .options(selectinload(Location.location_group))  # type: ignore[arg-type]
            )
            result = await session.execute(statement)
            location = result.scalars().first()

            if not location:
                raise ValueError(f"Location with id {location_id} not found")

            return location
        except Exception as e:
            self.logger.error(f"Failed to get location by id: {e!s}")
            raise e

    async def get_location_read_by_id(
        self, session: AsyncSession, location_id: UUID
    ) -> LocationRead:
        """Get a LocationRead with derived status populated.

        Wraps get_location_by_id with single-row batched lookups so the
        response includes status, assigned route, and delivery aggregates.
        Use this from routers that respond with LocationRead.
        """
        location = await self.get_location_by_id(session, location_id)
        ids = [location_id]
        future_set = await self.load_has_future_route_set(session, ids)
        assigned = await self.load_assigned_routes(session, ids)
        aggregates = await self.load_delivery_aggregates(session, ids)
        total, last_date = aggregates.get(location_id, (0, None))
        return self._to_read(
            location,
            has_future_route=location_id in future_set,
            assigned_route=assigned.get(location_id),
            last_delivery_date=last_date,
            total_deliveries=total,
        )

    async def get_locations(
        self,
        session: AsyncSession,
        pagination: PaginationParams,
        delivery_type: list[str] | None = None,
        status_filter: list[LocationStatusEnum] | None = None,
        location_group_id: list[UUID] | None = None,
    ) -> PaginatedResponse[LocationRead]:
        """Get paginated locations.

        Returns LocationRead objects with the derived ``status`` populated.
        Surfaces every location (no implicit ACTIVE-only filter); the
        three-state status (Active / Unscheduled / Inactive) is computed
        from in_roster + whether the location appears in a present/future
        route. Callers can narrow via the optional ``status_filter`` and
        ``delivery_type`` and ``location_group_id`` query params.
        """
        try:
            statement = (
                select(Location)
                .options(selectinload(Location.location_group))  # type: ignore[arg-type]
                .order_by(Location.created_at.desc())  # type: ignore[union-attr]
            )

            if delivery_type:
                statement = statement.where(
                    Location.delivery_type.in_(delivery_type)  # type: ignore[attr-defined]
                )

            if location_group_id:
                statement = statement.where(
                    col(Location.location_group_id).in_(location_group_id)
                )

            if status_filter:
                today_start = self._today_start()
                # Subquery: this location has a stop in a route whose group's
                # drive_date is today/future AND the route isn't yet frozen.
                is_scheduled = (
                    select(1)
                    .select_from(RouteStop)
                    .join(Route, Route.route_id == RouteStop.route_id)  # type: ignore[arg-type]
                    .join(
                        RouteGroup,
                        RouteGroup.route_group_id == Route.route_group_id,  # type: ignore[arg-type]
                    )
                    .outerjoin(
                        RouteSnapshot,
                        RouteSnapshot.route_id == Route.route_id,  # type: ignore[arg-type]
                    )
                    .where(RouteStop.location_id == Location.location_id)
                    .where(RouteGroup.drive_date >= today_start)
                    .where(col(RouteSnapshot.route_id).is_(None))
                    .exists()
                )
                status_conditions: list[Any] = []
                if LocationStatusEnum.ACTIVE in status_filter:
                    status_conditions.append(is_scheduled)
                if LocationStatusEnum.UNSCHEDULED in status_filter:
                    status_conditions.append(
                        and_(col(Location.in_roster).is_(True), ~is_scheduled)
                    )
                if LocationStatusEnum.INACTIVE in status_filter:
                    status_conditions.append(
                        and_(col(Location.in_roster).is_(False), ~is_scheduled)
                    )
                if status_conditions:
                    statement = statement.where(or_(*status_conditions))

            result, total = await paginate_query(session, statement, pagination)
            items = list(result.scalars().all())
            loc_ids = [loc.location_id for loc in items]
            future_set = await self.load_has_future_route_set(session, loc_ids)
            assigned = await self.load_assigned_routes(session, loc_ids)
            aggregates = await self.load_delivery_aggregates(session, loc_ids)
            reads = [
                self._to_read(
                    loc,
                    has_future_route=loc.location_id in future_set,
                    assigned_route=assigned.get(loc.location_id),
                    last_delivery_date=aggregates.get(loc.location_id, (0, None))[1],
                    total_deliveries=aggregates.get(loc.location_id, (0, None))[0],
                )
                for loc in items
            ]
            return PaginatedResponse.create(
                items=reads,
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
            )
        except Exception as e:
            self.logger.error(f"Failed to get locations: {e!s}")
            raise e

    async def get_delivery_types(self, session: AsyncSession) -> list[str]:
        """Return configured delivery types off the (always-present) settings row."""
        settings = await self.system_settings_service.require_settings(session)
        return settings.delivery_types

    async def validate_delivery_type(
        self, session: AsyncSession, delivery_type: str
    ) -> None:
        delivery_types = await self.get_delivery_types(session)
        if delivery_type not in delivery_types:
            allowed = ", ".join(delivery_types)
            raise InvalidDeliveryTypeError(
                f"Unknown delivery_type '{delivery_type}'. Allowed values: {allowed}"
            )

    async def validate_delivery_types(
        self, session: AsyncSession, delivery_types: Iterable[str]
    ) -> None:
        configured_delivery_types = await self.get_delivery_types(session)
        invalid_delivery_types = [
            delivery_type
            for delivery_type in delivery_types
            if delivery_type not in configured_delivery_types
        ]
        if invalid_delivery_types:
            allowed = ", ".join(configured_delivery_types)
            invalid = ", ".join(invalid_delivery_types)
            raise InvalidDeliveryTypeError(
                f"Unknown delivery_type '{invalid}'. Allowed values: {allowed}"
            )

    async def load_has_future_route_set(
        self, session: AsyncSession, location_ids: Iterable[UUID]
    ) -> set[UUID]:
        """Return the subset of ``location_ids`` that appear in any present/
        future route — i.e. a RouteStop whose Route is in a RouteGroup with
        drive_date >= today AND that Route is not yet frozen (no RouteSnapshot).

        One indexed query rather than per-location N+1.
        """
        ids = list(location_ids)
        if not ids:
            return set()
        today_start = self._today_start()
        statement = (
            select(RouteStop.location_id)
            .join(Route, Route.route_id == RouteStop.route_id)  # type: ignore[arg-type]
            .join(RouteGroup, RouteGroup.route_group_id == Route.route_group_id)  # type: ignore[arg-type]
            .outerjoin(
                RouteSnapshot,
                RouteSnapshot.route_id == Route.route_id,  # type: ignore[arg-type]
            )
            .where(col(RouteStop.location_id).in_(ids))
            .where(RouteGroup.drive_date >= today_start)
            .where(col(RouteSnapshot.route_id).is_(None))
            .distinct()
        )
        result = await session.execute(statement)
        return {row[0] for row in result.all()}

    async def load_assigned_routes(
        self, session: AsyncSession, location_ids: Iterable[UUID]
    ) -> dict[UUID, str]:
        """Return a mapping of location_id → route name for the soonest
        upcoming unfrozen route group each location appears in.

        One query rather than per-location N+1.
        """
        ids = list(location_ids)
        if not ids:
            return {}
        today_start = self._today_start()
        statement = (
            select(RouteStop.location_id, Route.name, RouteGroup.drive_date)
            .join(Route, Route.route_id == RouteStop.route_id)  # type: ignore[arg-type]
            .join(RouteGroup, RouteGroup.route_group_id == Route.route_group_id)  # type: ignore[arg-type]
            .outerjoin(
                RouteSnapshot,
                RouteSnapshot.route_id == Route.route_id,  # type: ignore[arg-type]
            )
            .where(col(RouteStop.location_id).in_(ids))
            .where(RouteGroup.drive_date >= today_start)
            .where(col(RouteSnapshot.route_id).is_(None))
            .order_by(col(RouteGroup.drive_date).asc())
        )
        result = await session.execute(statement)
        assigned: dict[UUID, str] = {}
        for loc_id, route_name, _ in result.all():
            if loc_id not in assigned:
                assigned[loc_id] = route_name
        return assigned

    async def load_delivery_aggregates(
        self, session: AsyncSession, location_ids: Iterable[UUID]
    ) -> dict[UUID, tuple[int, datetime | None]]:
        """Return a mapping of location_id → (total_deliveries, last_delivery_date)
        for completed deliveries (RouteStopSnapshot exists).

        One query rather than per-location N+1.
        """
        ids = list(location_ids)
        if not ids:
            return {}
        statement = (
            select(
                RouteStop.location_id,
                func.count().label("total"),
                func.max(RouteGroup.drive_date).label("last_date"),
            )
            .join(
                RouteStopSnapshot,
                RouteStopSnapshot.route_stop_id == RouteStop.route_stop_id,  # type: ignore[arg-type]
            )
            .join(Route, Route.route_id == RouteStop.route_id)  # type: ignore[arg-type]
            .join(RouteGroup, RouteGroup.route_group_id == Route.route_group_id)  # type: ignore[arg-type]
            .where(col(RouteStop.location_id).in_(ids))
            .group_by(col(RouteStop.location_id))
        )
        result = await session.execute(statement)
        return {row[0]: (row[1], row[2]) for row in result.all()}

    def _to_read(
        self,
        loc: Location,
        has_future_route: bool,
        assigned_route: str | None = None,
        last_delivery_date: datetime | None = None,
        total_deliveries: int = 0,
    ) -> LocationRead:
        """Build a LocationRead with the derived has_future_route populated.

        Status is then a @computed_field on LocationRead; no separate work
        needed at the service layer.
        """
        read = LocationRead.model_validate(loc, from_attributes=True)
        read.has_future_route = has_future_route
        read.assigned_route = assigned_route
        read.last_delivery_date = last_delivery_date
        read.total_deliveries = total_deliveries
        return read

    async def create_location(
        self, session: AsyncSession, location_data: LocationCreate
    ) -> Location:
        """Create a new location using a LocationCreate object - returns SQLModel instance"""
        try:
            await self.validate_delivery_type(session, location_data.delivery_type)
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
            # Reload with location_group eager-loaded so serializing to
            # LocationRead (location_group_name) doesn't lazy-load post-commit.
            return await self.get_location_by_id(session, location.location_id)
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
            if "delivery_type" in updated_data:
                await self.validate_delivery_type(
                    session, updated_data["delivery_type"]
                )
            for field, value in updated_data.items():
                setattr(location, field, value)

            await session.commit()
            # Reload with location_group eager-loaded so serializing to
            # LocationRead (location_group_name) doesn't lazy-load post-commit.
            return await self.get_location_by_id(session, location_id)

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
        """Delete location by ID.

        A location referenced by any route stop (past or future) cannot be
        hard-deleted — the FK would reject it anyway; this surfaces a clean
        LocationInUseError (409) with the referencing routes instead of a
        raw IntegrityError 500. Use in_roster=False to retire a location
        that has delivery history.
        """
        try:
            statement = select(Location).where(Location.location_id == location_id)
            result = await session.execute(statement)
            location = result.scalars().first()

            if not location:
                raise ValueError(f"Location with id {location_id} not found")

            referencing = await session.execute(
                select(Route.name, RouteGroup.drive_date)
                .select_from(RouteStop)
                .join(Route, Route.route_id == RouteStop.route_id)  # type: ignore[arg-type]
                .join(
                    RouteGroup,
                    RouteGroup.route_group_id == Route.route_group_id,  # type: ignore[arg-type]
                )
                .where(RouteStop.location_id == location_id)
                .order_by(col(RouteGroup.drive_date))
            )
            references = referencing.all()
            if references:
                routes_desc = ", ".join(
                    f"'{name}' ({drive_date.date()})"
                    for name, drive_date in references[:5]
                )
                more = f" and {len(references) - 5} more" if len(references) > 5 else ""
                raise LocationInUseError(
                    f"Location is used by {len(references)} route(s): "
                    f"{routes_desc}{more}. Set in_roster to false to retire "
                    f"it instead of deleting."
                )

            await session.delete(location)
            await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to delete location by id: {e!s}")
            await session.rollback()
            raise e

    async def review_locations(
        self,
        session: AsyncSession,
        file: UploadFile,
        column_map: dict[str, str],
    ) -> LocationImportResponse:
        """Review a pending location import: validate rows + (eventually) compute diff against existing locations.

        Side effect: persists `column_map` to system_settings so it becomes the
        default mapping on the next import.
        """
        try:
            await self.system_settings_service.set_import_column_map(
                session, column_map
            )
            await session.commit()
            df = await self._read_upload_file(file)
            rows: list[LocationImportRow] = []

            # track local duplicates
            full_dup_keys: dict[tuple[str, str, str], int] = {}
            address_keys: dict[str, int] = {}
            phone_keys: dict[str, int] = {}

            for index, row in df.iterrows():
                row_num = int(index) + 1  # type: ignore[call-overload]
                location = self._parse_row(row, column_map)
                alerts: list[AlertCode] = []

                # missing required fields
                if not self._has_required_fields(location):
                    alerts.append(AlertCode.MISSING_FIELDS)
                    rows.append(
                        LocationImportRow(row=row_num, location=location, alerts=alerts)
                    )
                    continue

                # invalid phone number format
                try:
                    location.phone_primary = validate_phone(location.phone_primary)
                    if location.phone_secondary:
                        location.phone_secondary = validate_phone(
                            location.phone_secondary
                        )
                except ValueError:
                    alerts.append(AlertCode.INVALID_FORMAT)
                    rows.append(
                        LocationImportRow(row=row_num, location=location, alerts=alerts)
                    )
                    continue

                # missing delivery group
                if not location.delivery_group:
                    alerts.append(AlertCode.MISSING_DELIVERY_GROUP)

                # full duplicate (same contact name, address, and phone)
                full_key = (
                    location.contact_name,
                    location.address,
                    location.phone_primary,
                )
                if full_key in full_dup_keys:
                    alerts.append(AlertCode.LOCAL_DUPLICATE)
                else:
                    full_dup_keys[full_key] = row_num

                    # partial duplicate — same address or same phone
                    if (
                        location.address in address_keys
                        or location.phone_primary in phone_keys
                    ):
                        alerts.append(AlertCode.PARTIAL_DUPLICATE)
                    if location.address not in address_keys:
                        address_keys[location.address] = row_num
                    if location.phone_primary not in phone_keys:
                        phone_keys[location.phone_primary] = row_num

                rows.append(
                    LocationImportRow(row=row_num, location=location, alerts=alerts)
                )

            return LocationImportResponse(
                success=not any(r.alerts for r in rows),
                total_rows=len(rows),
                rows=rows,
            )
        except Exception as e:
            self.logger.error(f"Failed to validate locations: {e!s}")
            raise e

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
            phone_primary=get_value("phone_primary"),
            phone_secondary=get_value("phone_secondary"),
            num_children=parse_int("num_children"),
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
            and entry.phone_primary is not None
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
            name=location_data.name,
            contact_name=location_data.contact_name,
            address=location_data.address,
            phone_primary=location_data.phone_primary,
            phone_secondary=location_data.phone_secondary,
            longitude=location_data.longitude,
            latitude=location_data.latitude,
            place_id=location_data.place_id,
            halal=location_data.halal,
            dietary_restrictions=location_data.dietary_restrictions,
            num_children=location_data.num_children,
            delivery_type=location_data.delivery_type,
            in_roster=location_data.in_roster,
            notes=location_data.notes,
        )

    async def ingest_locations(
        self, session: AsyncSession, request: LocationIngestRequest
    ) -> LocationIngestResponse:
        """Persist net-new locations and mark stale ones out-of-roster.

        Stale rows are not deleted — they keep their note_chain so a future
        reappearance can revive them.
        """
        try:
            await self.validate_delivery_type(session, request.delivery_type)
            # Fetch and mark stale locations out-of-roster in one SELECT IN
            stale_ids = [loc.location_id for loc in request.stale]
            stale_db_rows: list[Location] = []
            if stale_ids:
                result = await session.execute(
                    select(Location).where(Location.location_id.in_(stale_ids))  # type: ignore[attr-defined]
                )
                stale_db_rows = list(result.scalars().all())
                for loc in stale_db_rows:
                    loc.in_roster = False

            archived = [
                self._to_read(loc, has_future_route=False) for loc in stale_db_rows
            ]

            if not request.net_new:
                await session.commit()
                # Recompute has_future_route for archived locations now that
                # we've committed (their roster bit changed, but route stops
                # didn't, so the answer is the same — we just want it accurate).
                future_set = await self.load_has_future_route_set(
                    session, [loc.location_id for loc in stale_db_rows]
                )
                archived = [
                    self._to_read(loc, has_future_route=loc.location_id in future_set)
                    for loc in stale_db_rows
                ]
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

            needed_names = sorted(
                {
                    entry.delivery_group
                    for entry in request.net_new
                    if entry.delivery_group
                    and entry.delivery_group not in group_by_name
                }
            )
            for name in needed_names:
                group = LocationGroup(name=name)  # type: ignore[call-arg]
                session.add(group)
                group_by_name[name] = group

            # Build and batch-insert new Location records, each with its own
            # NoteChain so ingested locations support notes like every other
            # creation path (see create_location).
            new_note_chains: list[NoteChain] = []
            new_locations: list[Location] = []
            for entry, geocode_result in zip(
                request.net_new, geocode_results, strict=True
            ):
                if not geocode_result:
                    raise ValueError(f"Geocoding failed for address: {entry.address}")

                note_chain = NoteChain(
                    read_permission=NotePermission.ALL,
                    write_permission=NotePermission.ALL,
                )
                new_note_chains.append(note_chain)

                new_locations.append(
                    Location(
                        name=entry.contact_name,
                        contact_name=entry.contact_name,
                        address=geocode_result.formatted_address,
                        phone_primary=entry.phone_primary,
                        phone_secondary=entry.phone_secondary,
                        longitude=geocode_result.longitude,
                        latitude=geocode_result.latitude,
                        place_id=geocode_result.place_id,
                        halal=entry.halal or False,
                        dietary_restrictions=entry.dietary_restrictions or "",
                        num_children=entry.num_children or 0,
                        delivery_type=request.delivery_type,
                        in_roster=True,
                        note_chain_id=note_chain.note_chain_id,
                        location_group_id=group_by_name[
                            entry.delivery_group
                        ].location_group_id,
                    )
                )

            session.add_all(new_note_chains)
            session.add_all(new_locations)
            await session.commit()

            for loc in new_locations:
                await session.refresh(loc)

            # Newly-created locations have no route stops yet, so
            # has_future_route is False by definition; same logic as before
            # for the (newly-marked) stale set.
            stale_future_set = await self.load_has_future_route_set(
                session, [loc.location_id for loc in stale_db_rows]
            )
            return LocationIngestResponse(
                created=[
                    self._to_read(loc, has_future_route=False) for loc in new_locations
                ],
                archived=[
                    self._to_read(
                        loc, has_future_route=loc.location_id in stale_future_set
                    )
                    for loc in stale_db_rows
                ],
            )
        except Exception as e:
            self.logger.error(f"Failed to ingest locations: {e!s}")
            await session.rollback()
            raise e

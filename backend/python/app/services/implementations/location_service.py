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
    ChangedEntry,
    ChangedFieldOptInt,
    ChangedFieldOptStr,
    ChangedFieldStr,
    DuplicateGroup,
    Location,
    LocationCreate,
    LocationImportEntry,
    LocationImportResponse,
    LocationImportRow,
    LocationIngestRequest,
    LocationIngestResponse,
    LocationRead,
    LocationUpdate,
    NetNewEntry,
    StaleEntry,
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
from app.services.implementations.location_import_validation import (
    collect_field_alerts,
    duplicate_matching_fields,
    entry_match_key,
    find_duplicate_index_groups,
    is_blank,
    is_same_location,
    location_match_key,
    match_score,
    present_str,
    try_normalize_phone,
)
from app.utilities.google_maps_client import GeocodeResult, GoogleMapsClient
from app.utilities.pagination import paginate_query

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

    async def review_locations(
        self,
        session: AsyncSession,
        file: UploadFile,
        column_map: dict[str, str],
    ) -> LocationImportResponse:
        """Review a pending location import: validate rows and classify changes.

        Side effect: persists `column_map` to system_settings so it becomes the
        default mapping on the next import.
        """
        try:
            await self.system_settings_service.set_import_column_map(
                session, column_map
            )
            await session.commit()
            df = await self._read_upload_file(file)
            parsed_rows: list[tuple[int, LocationImportEntry]] = []

            for index, row in df.iterrows():
                row_num = int(index) + 1  # type: ignore[call-overload]
                parsed_rows.append((row_num, self._parse_row(row, column_map)))

            unique_addresses = {
                entry.address.strip()
                for _, entry in parsed_rows
                if present_str(entry.address)
            }
            known_valid_addresses = await self._existing_geocoded_addresses(
                session, unique_addresses
            )
            seen_addresses: set[str] = set()
            addresses_to_geocode: list[str] = []
            for _, entry in parsed_rows:
                if not present_str(entry.address):
                    continue
                address = entry.address.strip()
                if address in known_valid_addresses or address in seen_addresses:
                    continue
                seen_addresses.add(address)
                addresses_to_geocode.append(address)
            geocode_ok_by_address: dict[str, bool] = dict.fromkeys(
                known_valid_addresses, True
            )
            geocode_result_by_address: dict[str, GeocodeResult] = {}
            if addresses_to_geocode:
                geocoded = await asyncio.gather(
                    *(
                        self._geocode_import_address(address)
                        for address in addresses_to_geocode
                    )
                )
                geocode_ok_by_address.update(
                    {
                        address: result is not None
                        for address, result in zip(
                            addresses_to_geocode, geocoded, strict=True
                        )
                    }
                )
                geocode_result_by_address.update(
                    {
                        address: result
                        for address, result in zip(
                            addresses_to_geocode, geocoded, strict=True
                        )
                        if result is not None
                    }
                )

            phone_invalid_flags: list[bool] = []
            phone_secondary_invalid_flags: list[bool] = []
            for _, entry in parsed_rows:
                normalized_phone, phone_invalid = try_normalize_phone(
                    entry.phone_primary
                )
                if normalized_phone:
                    entry.phone_primary = normalized_phone
                normalized_secondary, secondary_invalid = try_normalize_phone(
                    entry.phone_secondary
                )
                if normalized_secondary:
                    entry.phone_secondary = normalized_secondary
                phone_invalid_flags.append(phone_invalid)
                phone_secondary_invalid_flags.append(secondary_invalid)

            entries = [entry for _, entry in parsed_rows]
            duplicate_index_groups = find_duplicate_index_groups(entries)
            duplicate_indices = {
                index for group in duplicate_index_groups for index in group
            }

            rows: list[LocationImportRow] = []
            for index, (row_num, entry) in enumerate(parsed_rows):
                geocode_ok: bool | None
                if is_blank(entry.address):
                    geocode_ok = None
                elif entry.address is not None:
                    address_key = entry.address.strip()
                    geocode_result = geocode_result_by_address.get(address_key)
                    if geocode_result is not None:
                        entry.address = geocode_result.formatted_address
                    geocode_ok = geocode_ok_by_address.get(address_key)
                else:
                    geocode_ok = None

                alerts = collect_field_alerts(
                    entry,
                    geocode_ok=geocode_ok,
                    phone_invalid=phone_invalid_flags[index],
                    phone_secondary_invalid=phone_secondary_invalid_flags[index],
                )
                if index in duplicate_indices:
                    alerts.append(AlertCode.LOCAL_DUPLICATE)

                rows.append(
                    LocationImportRow(row=row_num, location=entry, alerts=alerts)
                )

            duplicate_groups = []
            for group in duplicate_index_groups:
                matching_fields = {
                    field
                    for left_position, left_index in enumerate(group)
                    for right_index in group[left_position + 1 :]
                    for field in duplicate_matching_fields(
                        entries[left_index], entries[right_index]
                    )
                }
                duplicate_groups.append(
                    DuplicateGroup(
                        rows=[parsed_rows[i][0] for i in group],
                        matching_fields=sorted(
                            matching_fields, key=lambda field: field.value
                        ),
                    )
                )
            valid_rows = [
                (row.row, ValidatedLocationImportEntry.model_validate(row.location))
                for row in rows
                if not row.alerts and self._has_required_fields(row.location)
            ]
            net_new: list[NetNewEntry] = []
            stale: list[StaleEntry] = []
            changed: list[ChangedEntry] = []
            success = not any(r.alerts for r in rows)
            if success:
                net_new, stale, changed = await self._classify_import_rows(
                    session, valid_rows
                )

            return LocationImportResponse(
                success=success,
                total_rows=len(rows),
                rows=rows,
                duplicate_groups=duplicate_groups,
                net_new=net_new,
                stale=stale,
                changed=changed,
            )
        except Exception as e:
            self.logger.error(f"Failed to validate locations: {e!s}")
            raise e

    async def _existing_geocoded_addresses(
        self, session: AsyncSession, addresses: set[str]
    ) -> set[str]:
        """Return the subset of addresses that already exist on a geocoded Location.

        Exact match on Location.address (import side is already stripped). Only
        rows with latitude/longitude count as known-valid so we still geocode
        addresses that were stored without coordinates.
        """
        if not addresses:
            return set()

        result = await session.execute(
            select(Location.address).where(
                col(Location.address).in_(addresses),
                col(Location.latitude).is_not(None),
                col(Location.longitude).is_not(None),
            )
        )
        return {address for address in result.scalars().all() if address in addresses}

    async def _geocode_import_address(
        self, address: str | None
    ) -> GeocodeResult | None:
        """Geocode a non-blank import address; skip geocoding when address is missing."""
        if not present_str(address):
            return None
        return await self.google_maps_service.geocode_address(address)

    async def _classify_import_rows(
        self,
        session: AsyncSession,
        valid_rows: list[tuple[int, ValidatedLocationImportEntry]],
    ) -> tuple[list[NetNewEntry], list[StaleEntry], list[ChangedEntry]]:
        result = await session.execute(
            select(Location).options(selectinload(Location.location_group))  # type: ignore[arg-type]
        )
        existing_locations = list(result.scalars().all())
        matched_existing_ids: set[UUID] = set()
        net_new: list[NetNewEntry] = []
        changed: list[ChangedEntry] = []

        for row_num, entry in valid_rows:
            match = self._find_existing_import_match(
                entry,
                [
                    location
                    for location in existing_locations
                    if location.location_id not in matched_existing_ids
                ],
            )
            if match is None:
                net_new.append(self._to_net_new_entry(row_num, entry))
                continue

            matched_existing_ids.add(match.location_id)
            changed_entry = self._to_changed_entry(row_num, entry, match)
            if changed_entry is not None:
                changed.append(changed_entry)

        stale = [
            self._to_stale_entry(location)
            for location in existing_locations
            if location.in_roster and location.location_id not in matched_existing_ids
        ]
        return net_new, stale, changed

    def _find_existing_import_match(
        self,
        entry: ValidatedLocationImportEntry,
        existing_locations: list[Location],
    ) -> Location | None:
        """Best existing match by the 2-of-3 rule; ties keep table order."""
        entry_key = entry_match_key(entry)
        best_score = 0
        best_match: Location | None = None
        for location in existing_locations:
            location_key = location_match_key(location)
            if not is_same_location(entry_key, location_key):
                continue
            score = match_score(entry_key, location_key)
            if score > best_score:
                best_score = score
                best_match = location
        return best_match

    @staticmethod
    def _to_net_new_entry(
        row_num: int, entry: ValidatedLocationImportEntry
    ) -> NetNewEntry:
        return NetNewEntry(
            row=row_num,
            contact_name=entry.contact_name,
            address=entry.address,
            delivery_group=entry.delivery_group,
            phone_primary=entry.phone_primary,
            phone_secondary=entry.phone_secondary,
            num_children=entry.num_children,
        )

    @staticmethod
    def _to_stale_entry(location: Location) -> StaleEntry:
        return StaleEntry(
            location_id=location.location_id,
            contact_name=location.contact_name,
            address=location.address,
            delivery_group=location.location_group.name,
            phone_primary=location.phone_primary,
            phone_secondary=location.phone_secondary,
        )

    def _to_changed_entry(
        self, row_num: int, entry: ValidatedLocationImportEntry, location: Location
    ) -> ChangedEntry | None:
        old_delivery_group = location.location_group.name
        entry_key = entry_match_key(entry)
        location_key = location_match_key(location)
        contact_name_changed = entry_key.name != location_key.name
        address_changed = entry_key.address != location_key.address
        delivery_group_changed = entry.delivery_group != old_delivery_group
        phone_primary_changed = entry_key.phone != location_key.phone
        phone_secondary_changed = (entry.phone_secondary or None) != (
            location.phone_secondary or None
        )
        num_children_changed = (
            entry.num_children is not None
            and entry.num_children != location.num_children
        )
        roster_changed = not location.in_roster

        if not any(
            [
                contact_name_changed,
                address_changed,
                delivery_group_changed,
                phone_primary_changed,
                phone_secondary_changed,
                num_children_changed,
                roster_changed,
            ]
        ):
            return None

        return ChangedEntry(
            row=row_num,
            location_id=location.location_id,
            contact_name=entry.contact_name,
            address=ChangedFieldStr(new_value=entry.address, old_value=location.address)
            if address_changed
            else entry.address,
            delivery_group=ChangedFieldOptStr(
                new_value=entry.delivery_group, old_value=old_delivery_group
            )
            if delivery_group_changed
            else entry.delivery_group,
            phone_primary=ChangedFieldStr(
                new_value=entry.phone_primary, old_value=location.phone_primary
            )
            if phone_primary_changed
            else entry.phone_primary,
            phone_secondary=ChangedFieldOptStr(
                new_value=entry.phone_secondary, old_value=location.phone_secondary
            )
            if phone_secondary_changed
            else entry.phone_secondary,
            num_children=ChangedFieldOptInt(
                new_value=entry.num_children, old_value=location.num_children
            )
            if num_children_changed
            else location.num_children,
        )

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
        return (
            entry.contact_name is not None
            and entry.address is not None
            and entry.phone_primary is not None
            and entry.delivery_group is not None
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
        )

    async def ingest_locations(
        self, session: AsyncSession, request: LocationIngestRequest
    ) -> LocationIngestResponse:
        """Persist import merge results.

        Stale rows are not deleted. Address changes create a replacement
        location carrying over notes/history and mark the old row inactive.
        """
        try:
            await self.validate_delivery_type(session, request.delivery_type)
            changed_ids = [entry.location_id for entry in request.changed]
            if len(set(changed_ids)) != len(changed_ids):
                raise ValueError("Each changed location can only be included once")

            group_by_name = await self._ensure_location_groups_for_ingest(
                session, request
            )

            stale_ids = [loc.location_id for loc in request.stale]
            existing_ids = list(set(stale_ids + changed_ids))
            existing_by_id: dict[UUID, Location] = {}
            if existing_ids:
                result = await session.execute(
                    select(Location)
                    .where(Location.location_id.in_(existing_ids))  # type: ignore[attr-defined]
                    .options(selectinload(Location.location_group))  # type: ignore[arg-type]
                )
                existing_by_id = {
                    location.location_id: location
                    for location in result.scalars().all()
                }

            stale_db_rows: list[Location] = []
            for stale_id in stale_ids:
                loc = existing_by_id.get(stale_id)
                if loc is not None:
                    loc.in_roster = False
                    stale_db_rows.append(loc)

            geocode_results = await asyncio.gather(
                *[
                    self.google_maps_service.geocode_address(entry.address)
                    for entry in request.net_new
                ]
            )

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

            address_changed_entries = [
                entry
                for entry in request.changed
                if isinstance(entry.address, ChangedFieldStr)
            ]
            changed_geocode_results = await asyncio.gather(
                *[
                    self.google_maps_service.geocode_address(
                        self._changed_str_value(entry.address)
                    )
                    for entry in address_changed_entries
                ]
            )
            geocode_by_changed_id = {
                entry.location_id: geocode_result
                for entry, geocode_result in zip(
                    address_changed_entries, changed_geocode_results, strict=True
                )
            }

            for changed_entry in request.changed:
                location = existing_by_id.get(changed_entry.location_id)
                if location is None:
                    raise ValueError(
                        f"Location with id {changed_entry.location_id} was not found"
                    )

                delivery_group = self._changed_optional_str_value(
                    changed_entry.delivery_group
                )
                if not delivery_group:
                    raise ValueError("Changed location is missing delivery_group")

                if isinstance(changed_entry.address, ChangedFieldStr):
                    geocode_result = geocode_by_changed_id[changed_entry.location_id]
                    if not geocode_result:
                        raise ValueError(
                            f"Geocoding failed for address: {changed_entry.address.new_value}"
                        )
                    note_chain_id = location.note_chain_id
                    location.in_roster = False
                    location.note_chain_id = None
                    if location not in stale_db_rows:
                        stale_db_rows.append(location)
                    new_locations.append(
                        Location(
                            name=changed_entry.contact_name,
                            contact_name=changed_entry.contact_name,
                            address=geocode_result.formatted_address,
                            phone_primary=self._changed_str_value(
                                changed_entry.phone_primary
                            ),
                            phone_secondary=self._changed_optional_str_value(
                                changed_entry.phone_secondary
                            ),
                            longitude=geocode_result.longitude,
                            latitude=geocode_result.latitude,
                            place_id=geocode_result.place_id,
                            halal=location.halal,
                            dietary_restrictions=location.dietary_restrictions,
                            num_children=self._changed_optional_int_value(
                                changed_entry.num_children
                            )
                            or 0,
                            delivery_type=request.delivery_type,
                            in_roster=True,
                            note_chain_id=note_chain_id,
                            location_group_id=group_by_name[
                                delivery_group
                            ].location_group_id,
                        )
                    )
                    continue

                location.in_roster = True
                location.name = changed_entry.contact_name
                location.contact_name = changed_entry.contact_name
                location.phone_primary = self._changed_str_value(
                    changed_entry.phone_primary
                )
                location.phone_secondary = self._changed_optional_str_value(
                    changed_entry.phone_secondary
                )
                location.num_children = (
                    self._changed_optional_int_value(changed_entry.num_children) or 0
                )
                location.location_group_id = group_by_name[
                    delivery_group
                ].location_group_id

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

    async def _ensure_location_groups_for_ingest(
        self, session: AsyncSession, request: LocationIngestRequest
    ) -> dict[str, LocationGroup]:
        groups_result = await session.execute(select(LocationGroup))
        group_by_name: dict[str, LocationGroup] = {
            group.name: group for group in groups_result.scalars().all()
        }
        needed_names = {
            entry.delivery_group
            for entry in request.net_new
            if entry.delivery_group not in group_by_name
        }
        needed_names.update(
            delivery_group
            for delivery_group in (
                self._changed_optional_str_value(entry.delivery_group)
                for entry in request.changed
            )
            if delivery_group and delivery_group not in group_by_name
        )
        for name in sorted(needed_names):
            group = LocationGroup(name=name)  # type: ignore[call-arg]
            session.add(group)
            group_by_name[name] = group
        if needed_names:
            await session.flush()
        return group_by_name

    @staticmethod
    def _changed_str_value(value: str | ChangedFieldStr) -> str:
        if isinstance(value, ChangedFieldStr):
            return value.new_value
        return value

    @staticmethod
    def _changed_optional_str_value(
        value: str | None | ChangedFieldOptStr,
    ) -> str | None:
        if isinstance(value, ChangedFieldOptStr):
            return value.new_value
        return value

    @staticmethod
    def _changed_optional_int_value(
        value: int | None | ChangedFieldOptInt,
    ) -> int | None:
        if isinstance(value, ChangedFieldOptInt):
            return value.new_value
        return value

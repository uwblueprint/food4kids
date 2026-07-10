import logging

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.models.location import Location
from app.models.system_settings import (
    SystemSettings,
    SystemSettingsUpdate,
    _validate_delivery_types,
)
from app.utilities.google_maps_client import GoogleMapsClient


class DeliveryTypeInUseError(ValueError):
    """Raised when removing a delivery type that active locations still use."""


class DeliveryTypeRenameError(ValueError):
    """Raised when a delivery type rename is invalid (unknown, blank, or clash)."""


class SystemSettingsService:
    """Service for reading and writing the singleton SystemSettings row."""

    def __init__(self, logger: logging.Logger, google_maps_client: GoogleMapsClient):
        self.logger = logger
        self.google_maps_client = google_maps_client

    async def get_settings(self, session: AsyncSession) -> SystemSettings | None:
        """Return the SystemSettings row, or None if none has been created yet."""
        result = await session.execute(select(SystemSettings))
        return result.scalars().first()

    async def ensure_settings(self, session: AsyncSession) -> SystemSettings:
        """Guarantee the singleton settings row exists, creating it with model
        defaults if absent, and return it.

        Called once at startup so the rest of the app can treat "the settings
        row exists" as an invariant: config that lives on the row (e.g.
        ``delivery_types``) has a single source of truth and readers don't need
        a None-fallback. Idempotent — an existing row is left untouched.

        The server runs as a single process (see ``server.py``) with migrations
        applied before boot, so there's no insert race to guard against. Does
        not commit — the caller owns the surrounding transaction.
        """
        settings = await self.get_settings(session)
        if settings is not None:
            return settings

        settings = SystemSettings()
        session.add(settings)
        await session.flush()
        return settings

    async def require_settings(self, session: AsyncSession) -> SystemSettings:
        """Return the singleton settings row, asserting the startup invariant.

        ``ensure_settings`` creates the row at startup (see ``app.__init__``), so
        every other code path can treat its existence as a given. A missing row
        here is a broken invariant, not a state to paper over with defaults —
        fail loudly rather than silently substituting fallback config.
        """
        settings = await self.get_settings(session)
        if settings is None:
            raise RuntimeError(
                "SystemSettings row is missing; it must be created at startup "
                "via ensure_settings()."
            )
        return settings

    async def _count_active_locations_with_type(
        self, session: AsyncSession, delivery_type: str
    ) -> int:
        """Count locations still on the roster (Active or Unscheduled) that use
        ``delivery_type``.

        ``in_roster`` is the stored bit behind the derived status: in_roster
        locations are the ones that would break if their type vanished (they go
        filter-invisible and can no longer round-trip through edit/import).
        Inactive locations (in_roster=False) keep their historical string
        untouched, so they don't block removal.
        """
        stmt = (
            select(func.count())
            .select_from(Location)
            .where(col(Location.delivery_type) == delivery_type)
            .where(col(Location.in_roster).is_(True))
        )
        result = await session.execute(stmt)
        return result.scalar_one()

    async def _guard_delivery_type_removal(
        self, session: AsyncSession, old: list[str], new: list[str]
    ) -> None:
        """Block a settings update that drops a delivery type still in active use."""
        new_set = set(new)
        removed = [dtype for dtype in old if dtype not in new_set]
        in_use: dict[str, int] = {}
        for dtype in removed:
            count = await self._count_active_locations_with_type(session, dtype)
            if count:
                in_use[dtype] = count
        if in_use:
            detail = ", ".join(
                f"'{dtype}' ({count} active location{'s' if count != 1 else ''})"
                for dtype, count in in_use.items()
            )
            raise DeliveryTypeInUseError(
                f"Cannot remove delivery type(s) still in active use: {detail}. "
                "Reassign or deactivate those locations first, or rename the type."
            )

    async def update_settings(
        self, session: AsyncSession, settings_data: SystemSettingsUpdate
    ) -> SystemSettings:
        """Patch the singleton settings row (guaranteed to exist at startup).

        The warehouse coordinates are derived, not trusted: whenever
        ``warehouse_location`` is part of the patch, geocoding is the single
        source of truth for ``warehouse_latitude`` / ``warehouse_longitude``.
        A non-empty address is geocoded — normalizing the stored address to
        Google's formatted form and overwriting the coordinates, or raising
        ``ValueError`` if it can't be resolved — while clearing the address to
        ``None`` clears both coordinates. Any coordinates sent in the same
        patch are ignored.
        """
        updates = settings_data.model_dump(exclude_unset=True)

        if "warehouse_location" in updates:
            # Coordinates are derived from the address, never client-supplied.
            updates.pop("warehouse_latitude", None)
            updates.pop("warehouse_longitude", None)
            address = updates["warehouse_location"]
            if address is None:
                updates["warehouse_latitude"] = None
                updates["warehouse_longitude"] = None
            else:
                geocode_result = await self.google_maps_client.geocode_address(address)
                if geocode_result is None:
                    raise ValueError(
                        f"Geocoding failed for warehouse location: {address}"
                    )
                updates["warehouse_location"] = geocode_result.formatted_address
                updates["warehouse_latitude"] = geocode_result.latitude
                updates["warehouse_longitude"] = geocode_result.longitude

        settings = await self.require_settings(session)

        if "delivery_types" in updates:
            await self._guard_delivery_type_removal(
                session, old=settings.delivery_types, new=updates["delivery_types"]
            )

        for field_name, value in updates.items():
            setattr(settings, field_name, value)
        return settings

    async def rename_delivery_type(
        self, session: AsyncSession, old_name: str, new_name: str
    ) -> SystemSettings:
        """Rename a configured delivery type in place.

        Cascades onto every location referencing ``old_name`` — active *and*
        inactive, since a rename preserves the type's identity — then swaps the
        name in the settings list (order preserved).
        """
        new_name = new_name.strip()
        if not new_name:
            raise DeliveryTypeRenameError("New delivery type name must not be blank")

        settings = await self.require_settings(session)
        current = settings.delivery_types
        if old_name not in current:
            raise DeliveryTypeRenameError(f"Unknown delivery type '{old_name}'")
        if new_name == old_name:
            raise DeliveryTypeRenameError(
                "New delivery type name must differ from the current name"
            )
        if new_name in current:
            raise DeliveryTypeRenameError(f"Delivery type '{new_name}' already exists")

        renamed = _validate_delivery_types(
            [new_name if dtype == old_name else dtype for dtype in current]
        )

        await session.execute(
            update(Location)
            .where(col(Location.delivery_type) == old_name)
            .values(delivery_type=new_name)
        )

        settings.delivery_types = renamed
        return settings

    async def set_import_column_map(
        self, session: AsyncSession, column_map: dict[str, str]
    ) -> None:
        """Persist the import column map onto the (always-present) settings row.

        Caller is responsible for committing the surrounding transaction.
        """
        await self.update_settings(
            session, SystemSettingsUpdate(import_column_map=column_map)
        )

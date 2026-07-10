import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.system_settings import SystemSettings, SystemSettingsUpdate
from app.utilities.google_maps_client import GoogleMapsClient


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

    async def update_settings(
        self, session: AsyncSession, settings_data: SystemSettingsUpdate
    ) -> SystemSettings:
        """Patch the singleton settings row, creating it if needed.

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

        settings = await self.get_settings(session)

        if settings is None:
            settings = SystemSettings(**updates)
            session.add(settings)
            return settings

        for field_name, value in updates.items():
            setattr(settings, field_name, value)
        return settings

    async def set_import_column_map(
        self, session: AsyncSession, column_map: dict[str, str]
    ) -> None:
        """Persist the import column map, creating the row if it doesn't exist yet.

        Caller is responsible for committing the surrounding transaction.
        """
        await self.update_settings(
            session, SystemSettingsUpdate(import_column_map=column_map)
        )

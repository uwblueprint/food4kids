"""Tests for SystemSettingsService — the startup invariant that guarantees the
singleton settings row always exists, and the geocoding of the warehouse
location on update.
"""

import logging
from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.system_settings import SystemSettings, SystemSettingsUpdate
from app.services.implementations.system_settings_service import SystemSettingsService
from app.utilities.google_maps_client import GeocodeResult, GoogleMapsClient


class _FakeMapsClient:
    """Stand-in for GoogleMapsClient that returns a preset geocode result and
    records the addresses it was asked to resolve."""

    def __init__(self, result: GeocodeResult | None = None) -> None:
        self.result = result
        self.calls: list[str] = []

    async def geocode_address(self, address: str) -> GeocodeResult | None:
        self.calls.append(address)
        return self.result


def _service(maps_client: _FakeMapsClient | None = None) -> SystemSettingsService:
    return SystemSettingsService(
        logging.getLogger("test"),
        cast("GoogleMapsClient", maps_client or _FakeMapsClient()),
    )


async def _count_settings(session: AsyncSession) -> int:
    result = await session.execute(select(SystemSettings))
    return len(result.scalars().all())


@pytest.mark.asyncio
async def test_ensure_settings_creates_row_when_absent(
    test_session: AsyncSession,
) -> None:
    """With no settings row, ensure_settings creates one with model defaults."""
    service = _service()
    assert await service.get_settings(test_session) is None

    created = await service.ensure_settings(test_session)

    # Persisted with model defaults (boxes_per_car defaults to 10).
    assert created.system_settings_id is not None
    assert created.boxes_per_car == 10
    assert await _count_settings(test_session) == 1


@pytest.mark.asyncio
async def test_ensure_settings_is_idempotent_and_preserves_existing(
    test_session: AsyncSession,
) -> None:
    """A second call is a no-op — it returns the existing row untouched rather
    than resetting it to defaults or inserting a duplicate."""
    service = _service()

    first = await service.ensure_settings(test_session)
    first.boxes_per_car = 42
    await test_session.flush()

    second = await service.ensure_settings(test_session)

    assert second.system_settings_id == first.system_settings_id
    assert second.boxes_per_car == 42
    assert await _count_settings(test_session) == 1


_GEOCODE_RESULT = GeocodeResult(
    formatted_address="123 Main St, Waterloo, ON N2L 3G1, Canada",
    place_id="place-abc",
    latitude=43.4643,
    longitude=-80.5204,
)


@pytest.mark.asyncio
async def test_update_settings_geocodes_warehouse_location(
    test_session: AsyncSession,
) -> None:
    """Setting warehouse_location geocodes it, normalizing the stored address
    and deriving the coordinates."""
    maps = _FakeMapsClient(_GEOCODE_RESULT)
    service = _service(maps)

    settings = await service.update_settings(
        test_session, SystemSettingsUpdate(warehouse_location="123 main st waterloo")
    )

    assert maps.calls == ["123 main st waterloo"]
    assert settings.warehouse_location == _GEOCODE_RESULT.formatted_address
    assert settings.warehouse_latitude == _GEOCODE_RESULT.latitude
    assert settings.warehouse_longitude == _GEOCODE_RESULT.longitude


@pytest.mark.asyncio
async def test_update_settings_ignores_client_supplied_coords(
    test_session: AsyncSession,
) -> None:
    """Coordinates are derived from geocoding, so any lat/lng sent alongside the
    address is ignored rather than trusted."""
    maps = _FakeMapsClient(_GEOCODE_RESULT)
    service = _service(maps)

    settings = await service.update_settings(
        test_session,
        SystemSettingsUpdate(
            warehouse_location="123 main st waterloo",
            warehouse_latitude=0.0,
            warehouse_longitude=0.0,
        ),
    )

    assert settings.warehouse_latitude == _GEOCODE_RESULT.latitude
    assert settings.warehouse_longitude == _GEOCODE_RESULT.longitude


@pytest.mark.asyncio
async def test_update_settings_invalid_address_raises(
    test_session: AsyncSession,
) -> None:
    """An address the geocoder can't resolve fails the patch rather than
    silently storing coordinate-less warehouse data."""
    maps = _FakeMapsClient(None)
    service = _service(maps)

    with pytest.raises(ValueError, match="Geocoding failed"):
        await service.update_settings(
            test_session, SystemSettingsUpdate(warehouse_location="nowhere at all")
        )

    # The failed patch persisted nothing.
    assert await _count_settings(test_session) == 0


@pytest.mark.asyncio
async def test_update_settings_clearing_location_clears_coords(
    test_session: AsyncSession,
) -> None:
    """Clearing warehouse_location to None clears the coordinates too, without
    calling the geocoder."""
    maps = _FakeMapsClient(_GEOCODE_RESULT)
    service = _service(maps)

    await service.update_settings(
        test_session, SystemSettingsUpdate(warehouse_location="123 main st waterloo")
    )
    await test_session.flush()

    settings = await service.update_settings(
        test_session, SystemSettingsUpdate(warehouse_location=None)
    )

    assert settings.warehouse_location is None
    assert settings.warehouse_latitude is None
    assert settings.warehouse_longitude is None
    # The geocoder was only hit for the initial set, not the clear.
    assert maps.calls == ["123 main st waterloo"]


@pytest.mark.asyncio
async def test_update_settings_unrelated_patch_skips_geocoding(
    test_session: AsyncSession,
) -> None:
    """A patch that doesn't touch warehouse_location leaves coordinates alone
    and never calls the geocoder."""
    maps = _FakeMapsClient(_GEOCODE_RESULT)
    service = _service(maps)

    settings = await service.update_settings(
        test_session, SystemSettingsUpdate(default_cap=5)
    )

    assert settings.default_cap == 5
    assert settings.warehouse_location is None
    assert maps.calls == []

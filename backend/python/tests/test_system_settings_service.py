"""Tests for SystemSettingsService.ensure_settings — the startup invariant that
guarantees the singleton settings row always exists.
"""

import logging

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.system_settings import SystemSettings
from app.services.implementations.system_settings_service import SystemSettingsService


def _service() -> SystemSettingsService:
    return SystemSettingsService(logging.getLogger("test"))


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

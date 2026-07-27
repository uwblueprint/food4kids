"""Tests for the BaseModel timestamp convention: ``created_at``/``updated_at``
are stamped on insert, and ``updated_at`` is bumped on every update — via a
column-level ``onupdate`` that fires for both ORM flushes and Core ``update()``
statements. ``Job`` overrides ``updated_at`` and is exempt.
"""

from datetime import datetime

import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.models.job import Job
from app.models.system_settings import SystemSettings

# A fixed past instant used to backdate rows deterministically, so "did
# updated_at move to ~now?" doesn't hinge on sub-microsecond timing.
_PAST = datetime(2000, 1, 1, 12, 0, 0)


async def _make_settings(session: AsyncSession) -> SystemSettings:
    settings = SystemSettings()
    session.add(settings)
    await session.commit()
    return settings


async def _backdate(session: AsyncSession, settings: SystemSettings) -> None:
    """Set both timestamps to _PAST via an explicit Core update (which, by
    setting updated_at itself, deliberately bypasses onupdate)."""
    await session.execute(
        update(SystemSettings)
        .where(col(SystemSettings.system_settings_id) == settings.system_settings_id)
        .values(created_at=_PAST, updated_at=_PAST)
    )
    await session.commit()
    await session.refresh(settings)
    assert settings.created_at == _PAST
    assert settings.updated_at == _PAST


@pytest.mark.asyncio
async def test_timestamps_stamped_and_equal_on_insert(
    test_session: AsyncSession,
) -> None:
    """Both timestamps are set on insert and equal to within a microsecond."""
    settings = await _make_settings(test_session)

    assert settings.created_at is not None
    assert settings.updated_at is not None
    assert abs((settings.updated_at - settings.created_at).total_seconds()) < 0.001


@pytest.mark.asyncio
async def test_updated_at_bumps_on_orm_update(test_session: AsyncSession) -> None:
    """An ORM attribute change bumps updated_at and leaves created_at alone."""
    settings = await _make_settings(test_session)
    await _backdate(test_session, settings)

    settings.default_cap = 5
    await test_session.commit()
    await test_session.refresh(settings)

    assert settings.created_at == _PAST  # insert stamp is immutable
    assert settings.updated_at is not None and settings.updated_at > _PAST


@pytest.mark.asyncio
async def test_updated_at_bumps_on_core_bulk_update(
    test_session: AsyncSession,
) -> None:
    """A Core update() that doesn't set updated_at still bumps it (onupdate)."""
    settings = await _make_settings(test_session)
    await _backdate(test_session, settings)

    await test_session.execute(
        update(SystemSettings)
        .where(col(SystemSettings.system_settings_id) == settings.system_settings_id)
        .values(default_cap=7)
    )
    await test_session.commit()
    await test_session.refresh(settings)

    assert settings.updated_at is not None and settings.updated_at > _PAST


@pytest.mark.asyncio
async def test_explicit_updated_at_wins_over_onupdate(
    test_session: AsyncSession,
) -> None:
    """When a statement sets updated_at itself, onupdate does not override it."""
    settings = await _make_settings(test_session)
    await _backdate(test_session, settings)
    explicit = datetime(2010, 6, 15, 8, 30, 0)

    await test_session.execute(
        update(SystemSettings)
        .where(col(SystemSettings.system_settings_id) == settings.system_settings_id)
        .values(default_cap=9, updated_at=explicit)
    )
    await test_session.commit()
    await test_session.refresh(settings)

    assert settings.updated_at == explicit


@pytest.mark.asyncio
async def test_job_updated_at_is_not_auto_bumped(test_session: AsyncSession) -> None:
    """Job overrides updated_at (null until first set), so it is exempt from the
    auto-bump — its lifecycle sets the timestamp explicitly."""
    job = Job()
    test_session.add(job)
    await test_session.commit()
    await test_session.refresh(job)
    assert job.updated_at is None

    job.started_at = datetime(2021, 3, 3, 3, 3, 3)
    await test_session.commit()
    await test_session.refresh(job)

    assert job.updated_at is None

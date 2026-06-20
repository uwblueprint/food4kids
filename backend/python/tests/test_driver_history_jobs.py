"""Tests for the nightly driver-history job (freeze + mileage aggregation).

The job opens its own session via the module-global session maker and reads
date.today(), so we point that global at the test engine (monkeypatch) and
seed today's data with committed rows the job's separate session can see.
"""

from datetime import date, datetime
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import select

from app.models.driver import Driver
from app.models.driver_history import DriverHistory
from app.models.enum import DeliveryTypeEnum
from app.models.location import Location
from app.models.location_group import LocationGroup
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_snapshot import RouteSnapshot
from app.models.route_stop import RouteStop
from app.models.route_stop_snapshot import RouteStopSnapshot
from app.models.system_settings import SystemSettings
from app.models.user import User
from app.services.jobs import driver_history_jobs

ROUTE_KM = 12.5


async def _seed_today(maker: async_sessionmaker[AsyncSession]) -> dict[str, Any]:
    """Seed (committed) an active driver assigned to a frozen-able route that
    runs today, visiting one geocoded location, with warehouse coords set."""
    async with maker() as s:
        group = LocationGroup(name="G", color="#fff", notes="")
        user = User(
            first_name="Test",
            last_name="Driver",
            email="drv@test.dev",
            auth_id="drv-uid",
        )
        settings = SystemSettings(
            warehouse_location="Warehouse",
            warehouse_latitude=43.0,
            warehouse_longitude=-80.0,
        )
        s.add_all([group, user, settings])
        await s.commit()
        await s.refresh(group)
        await s.refresh(user)

        driver = Driver(
            user_id=user.user_id,
            phone="+12125551234",
            address="1 Depot Rd",
            license_plate="DRV1",
            car_make_model="Toyota Corolla",
            active=True,
        )
        loc = Location(
            location_group_id=group.location_group_id,
            name="Fam",
            contact_name="Fam",
            address="1 A St",
            phone_primary="+12125550001",
            latitude=43.1,
            longitude=-80.1,
            num_children=6,
            delivery_type=DeliveryTypeEnum.FAMILY,
        )
        # drive_date is today so the job (date.today()) picks it up.
        rg = RouteGroup(
            name="Today",
            drive_date=datetime.combine(date.today(), datetime.min.time()),
        )
        s.add_all([driver, loc, rg])
        await s.commit()
        await s.refresh(driver)
        await s.refresh(loc)
        await s.refresh(rg)

        route = Route(
            name="R1",
            length=ROUTE_KM,
            route_group_id=rg.route_group_id,
            driver_id=driver.driver_id,
        )
        s.add(route)
        await s.commit()
        await s.refresh(route)
        s.add(
            RouteStop(
                route_id=route.route_id,
                location_id=loc.location_id,
                stop_number=1,
            )
        )
        await s.commit()
        return {"driver_id": driver.driver_id, "route_id": route.route_id}


async def _counts(maker: async_sessionmaker[AsyncSession]) -> dict[str, Any]:
    async with maker() as s:
        snaps = (await s.execute(select(RouteSnapshot))).scalars().all()
        stop_snaps = (await s.execute(select(RouteStopSnapshot))).scalars().all()
        histories = (await s.execute(select(DriverHistory))).scalars().all()
        return {
            "snapshots": len(snaps),
            "stop_snapshots": len(stop_snaps),
            "km": sum(h.km for h in histories),
            "history_rows": len(histories),
        }


@pytest.mark.asyncio
async def test_freeze_and_aggregate_then_idempotent(
    test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """First run freezes today's route + aggregates its mileage; a second run
    is a no-op (no duplicate snapshots, km not double-counted)."""
    maker = async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    monkeypatch.setattr(driver_history_jobs, "async_session_maker_instance", maker)

    await _seed_today(maker)

    # First run: freeze + aggregate.
    await driver_history_jobs.process_daily_driver_history()
    after_first = await _counts(maker)
    assert after_first["snapshots"] == 1
    assert after_first["stop_snapshots"] == 1
    assert after_first["history_rows"] == 1
    assert after_first["km"] == pytest.approx(ROUTE_KM)

    # Second run: nothing newly frozen -> no new snapshots, km unchanged.
    await driver_history_jobs.process_daily_driver_history()
    after_second = await _counts(maker)
    assert after_second["snapshots"] == 1
    assert after_second["stop_snapshots"] == 1
    assert after_second["km"] == pytest.approx(ROUTE_KM)  # NOT 2 * ROUTE_KM


@pytest.mark.asyncio
async def test_no_freeze_when_warehouse_unconfigured(
    test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without warehouse coords the job can't freeze, so no snapshots and no
    mileage are recorded (the run is degraded and logs a warning)."""
    maker = async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    monkeypatch.setattr(driver_history_jobs, "async_session_maker_instance", maker)

    await _seed_today(maker)
    # Blank out the warehouse coords seeded above.
    async with maker() as s:
        settings = (await s.execute(select(SystemSettings))).scalars().first()
        assert settings is not None
        settings.warehouse_location = None
        settings.warehouse_latitude = None
        settings.warehouse_longitude = None
        await s.commit()

    await driver_history_jobs.process_daily_driver_history()
    after = await _counts(maker)
    assert after["snapshots"] == 0
    assert after["history_rows"] == 0

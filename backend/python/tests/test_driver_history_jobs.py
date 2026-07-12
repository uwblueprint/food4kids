"""Tests for the nightly route-freeze job.

The job creates snapshots only — mileage is derived at read time from
frozen routes, so freezing a route is what makes it count. The job opens
its own sessions via the module-global session maker and reads
date.today(), so we point that global at the test engine (monkeypatch) and
seed data with committed rows the job's separate sessions can see.
"""

from datetime import date, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import select

from app.models.driver import Driver
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


async def _seed(
    maker: async_sessionmaker[AsyncSession],
    *,
    drive_date: date | None = None,
    assign_driver: bool = True,
) -> dict[str, Any]:
    """Seed (committed) an active driver + a freezable route on the given
    drive_date (default today), visiting one geocoded location, with
    warehouse coords set. Reuses shared rows if called more than once."""
    the_date = drive_date or date.today()
    async with maker() as s:
        settings = (await s.execute(select(SystemSettings))).scalars().first()
        if settings is None:
            s.add(
                SystemSettings(
                    warehouse_location="Warehouse",
                    warehouse_latitude=43.0,
                    warehouse_longitude=-80.0,
                )
            )

        group = (await s.execute(select(LocationGroup))).scalars().first()
        if group is None:
            group = LocationGroup(name="G", color="#fff", notes="")
            s.add(group)
            await s.commit()
            await s.refresh(group)

        user = User(
            first_name="Test",
            last_name=f"Driver{the_date.isoformat()}",
            email=f"drv-{the_date.isoformat()}-{assign_driver}@test.dev",
            auth_id=f"drv-uid-{the_date.isoformat()}-{assign_driver}",
        )
        s.add(user)
        await s.commit()
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
            delivery_type="Family",
        )
        rg = RouteGroup(
            name=f"Group {the_date.isoformat()}",
            drive_date=datetime.combine(the_date, datetime.min.time()),
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
            driver_id=driver.driver_id if assign_driver else None,
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
        return {
            "snapshots": len(snaps),
            "stop_snapshots": len(stop_snaps),
            "snapshot_route_ids": {snap.route_id for snap in snaps},
        }


def _maker(test_db_engine: Any) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.mark.asyncio
async def test_freeze_then_idempotent(
    test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """First run freezes today's route; a second run is a no-op (no
    duplicate snapshots)."""
    maker = _maker(test_db_engine)
    monkeypatch.setattr(driver_history_jobs, "async_session_maker_instance", maker)

    await _seed(maker)

    await driver_history_jobs.process_daily_driver_history()
    after_first = await _counts(maker)
    assert after_first["snapshots"] == 1
    assert after_first["stop_snapshots"] == 1

    await driver_history_jobs.process_daily_driver_history()
    after_second = await _counts(maker)
    assert after_second["snapshots"] == 1
    assert after_second["stop_snapshots"] == 1


@pytest.mark.asyncio
async def test_catch_up_freezes_missed_past_dates(
    test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A past-dated un-frozen route (e.g. the server was down at 23:59 that
    night) is swept up by the next run — its mileage starts counting as soon
    as it's frozen, under its own drive_date month."""
    maker = _maker(test_db_engine)
    monkeypatch.setattr(driver_history_jobs, "async_session_maker_instance", maker)

    seeded = await _seed(maker, drive_date=date.today() - timedelta(days=3))

    await driver_history_jobs.process_daily_driver_history()

    after = await _counts(maker)
    assert after["snapshots"] == 1
    assert after["snapshot_route_ids"] == {seeded["route_id"]}


@pytest.mark.asyncio
async def test_future_routes_not_frozen(
    test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    maker = _maker(test_db_engine)
    monkeypatch.setattr(driver_history_jobs, "async_session_maker_instance", maker)

    await _seed(maker, drive_date=date.today() + timedelta(days=2))

    await driver_history_jobs.process_daily_driver_history()
    after = await _counts(maker)
    assert after["snapshots"] == 0


@pytest.mark.asyncio
async def test_driverless_route_still_frozen(
    test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A driverless route is still frozen — the delivery is a historical
    fact. It just derives to no one's mileage until someone is assigned."""
    maker = _maker(test_db_engine)
    monkeypatch.setattr(driver_history_jobs, "async_session_maker_instance", maker)

    await _seed(maker, assign_driver=False)

    await driver_history_jobs.process_daily_driver_history()
    after = await _counts(maker)
    assert after["snapshots"] == 1
    assert after["stop_snapshots"] == 1


@pytest.mark.asyncio
async def test_warehouse_unconfigured_self_heals(
    test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without warehouse coords the job freezes nothing — and the routes
    stay due, so the first run after coords are set picks them up."""
    maker = _maker(test_db_engine)
    monkeypatch.setattr(driver_history_jobs, "async_session_maker_instance", maker)

    await _seed(maker)
    async with maker() as s:
        settings = (await s.execute(select(SystemSettings))).scalars().first()
        assert settings is not None
        settings.warehouse_location = None
        settings.warehouse_latitude = None
        settings.warehouse_longitude = None
        await s.commit()

    await driver_history_jobs.process_daily_driver_history()
    assert (await _counts(maker))["snapshots"] == 0

    async with maker() as s:
        settings = (await s.execute(select(SystemSettings))).scalars().first()
        assert settings is not None
        settings.warehouse_location = "Warehouse"
        settings.warehouse_latitude = 43.0
        settings.warehouse_longitude = -80.0
        await s.commit()

    await driver_history_jobs.process_daily_driver_history()
    assert (await _counts(maker))["snapshots"] == 1


@pytest.mark.asyncio
async def test_failing_route_does_not_poison_the_run(
    test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One route failing to freeze must not stop other due routes from
    being frozen in the same run (per-route sessions/transactions)."""
    maker = _maker(test_db_engine)
    monkeypatch.setattr(driver_history_jobs, "async_session_maker_instance", maker)

    poisoned = await _seed(maker, drive_date=date.today() - timedelta(days=1))
    healthy = await _seed(maker)

    real_freeze = driver_history_jobs._freeze_route

    async def failing_freeze(maker_: Any, route_id: Any, *args: Any) -> None:
        if route_id == poisoned["route_id"]:
            raise RuntimeError("injected freeze failure")
        await real_freeze(maker_, route_id, *args)

    monkeypatch.setattr(driver_history_jobs, "_freeze_route", failing_freeze)

    await driver_history_jobs.process_daily_driver_history()

    after = await _counts(maker)
    assert after["snapshot_route_ids"] == {healthy["route_id"]}

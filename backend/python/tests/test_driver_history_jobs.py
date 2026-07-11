"""Tests for the nightly driver-history job (freeze + mileage ledger credit).

The job opens its own session via the module-global session maker and reads
date.today(), so we point that global at the test engine (monkeypatch) and
seed data with committed rows the job's separate session can see.
"""

from datetime import date, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import select

from app.models.driver import Driver
from app.models.driver_history import DriverHistory
from app.models.enum import MileageEntryKindEnum
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
        entries = (await s.execute(select(DriverHistory))).scalars().all()
        return {
            "snapshots": len(snaps),
            "stop_snapshots": len(stop_snaps),
            "km": sum(e.km for e in entries),
            "entries": entries,
            "entry_rows": len(entries),
        }


def _maker(test_db_engine: Any) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.mark.asyncio
async def test_freeze_and_credit_then_idempotent(
    test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """First run freezes today's route + posts an AUTO ledger credit; a second
    run is a no-op (no duplicate snapshots, km not double-counted)."""
    maker = _maker(test_db_engine)
    monkeypatch.setattr(driver_history_jobs, "async_session_maker_instance", maker)

    seeded = await _seed(maker)

    # First run: freeze + credit.
    await driver_history_jobs.process_daily_driver_history()
    after_first = await _counts(maker)
    assert after_first["snapshots"] == 1
    assert after_first["stop_snapshots"] == 1
    assert after_first["entry_rows"] == 1
    assert after_first["km"] == pytest.approx(ROUTE_KM)

    entry = after_first["entries"][0]
    assert entry.kind == MileageEntryKindEnum.AUTO
    assert entry.driver_id == seeded["driver_id"]
    assert entry.route_id == seeded["route_id"]
    assert entry.drive_date == date.today()

    # The snapshot locks in the credited length.
    async with maker() as s:
        snap = (await s.execute(select(RouteSnapshot))).scalars().one()
        assert snap.length_km == pytest.approx(ROUTE_KM)

    # Second run: nothing newly frozen -> no new snapshots, km unchanged.
    await driver_history_jobs.process_daily_driver_history()
    after_second = await _counts(maker)
    assert after_second["snapshots"] == 1
    assert after_second["stop_snapshots"] == 1
    assert after_second["km"] == pytest.approx(ROUTE_KM)  # NOT 2 * ROUTE_KM


@pytest.mark.asyncio
async def test_catch_up_freezes_missed_past_dates(
    test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A past-dated un-frozen route (e.g. the server was down at 23:59 that
    night) is swept up by the next run, and its credit lands under the PAST
    drive_date — not the day the job happened to run."""
    maker = _maker(test_db_engine)
    monkeypatch.setattr(driver_history_jobs, "async_session_maker_instance", maker)

    three_days_ago = date.today() - timedelta(days=3)
    seeded = await _seed(maker, drive_date=three_days_ago)

    await driver_history_jobs.process_daily_driver_history()

    after = await _counts(maker)
    assert after["snapshots"] == 1
    assert after["entry_rows"] == 1
    entry = after["entries"][0]
    assert entry.drive_date == three_days_ago
    assert entry.km == pytest.approx(ROUTE_KM)
    assert entry.driver_id == seeded["driver_id"]


@pytest.mark.asyncio
async def test_unassigned_route_frozen_but_not_credited(
    test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A driverless route still gets frozen (the delivery is a historical
    fact) but posts no mileage credit — there is no one to credit."""
    maker = _maker(test_db_engine)
    monkeypatch.setattr(driver_history_jobs, "async_session_maker_instance", maker)

    await _seed(maker, assign_driver=False)

    await driver_history_jobs.process_daily_driver_history()

    after = await _counts(maker)
    assert after["snapshots"] == 1
    assert after["stop_snapshots"] == 1
    assert after["entry_rows"] == 0


@pytest.mark.asyncio
async def test_warehouse_unconfigured_self_heals(
    test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without warehouse coords the job freezes nothing — and the routes stay
    due, so the first run after coords are set picks them up (no km lost)."""
    maker = _maker(test_db_engine)
    monkeypatch.setattr(driver_history_jobs, "async_session_maker_instance", maker)

    await _seed(maker)
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
    assert after["entry_rows"] == 0

    # Configure the warehouse; the next run self-heals.
    async with maker() as s:
        settings = (await s.execute(select(SystemSettings))).scalars().first()
        assert settings is not None
        settings.warehouse_location = "Warehouse"
        settings.warehouse_latitude = 43.0
        settings.warehouse_longitude = -80.0
        await s.commit()

    await driver_history_jobs.process_daily_driver_history()
    healed = await _counts(maker)
    assert healed["snapshots"] == 1
    assert healed["entry_rows"] == 1
    assert healed["km"] == pytest.approx(ROUTE_KM)


@pytest.mark.asyncio
async def test_freeze_and_credit_are_atomic_per_route(
    test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the mileage credit can't be written, the route's snapshot must not
    be committed either (per-route transaction) — otherwise the route would
    look frozen and its km would be silently lost forever.

    Failure is injected for real: pre-inserting an AUTO ledger entry for the
    route makes the job's own AUTO insert violate the one-AUTO-per-route
    unique index, so the whole per-route transaction rolls back."""
    maker = _maker(test_db_engine)
    monkeypatch.setattr(driver_history_jobs, "async_session_maker_instance", maker)

    seeded = await _seed(maker)

    # Poison pill: an AUTO entry for this route already exists.
    async with maker() as s:
        s.add(
            DriverHistory(
                driver_id=seeded["driver_id"],
                route_id=seeded["route_id"],
                drive_date=date.today(),
                km=1.0,
                kind=MileageEntryKindEnum.AUTO,
            )
        )
        await s.commit()

    await driver_history_jobs.process_daily_driver_history()

    after = await _counts(maker)
    # The route failed to freeze atomically: no snapshot committed, and the
    # only ledger entry is the poison pill (km == 1.0, not 1.0 + ROUTE_KM).
    assert after["snapshots"] == 0
    assert after["entry_rows"] == 1
    assert after["km"] == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_failing_route_does_not_poison_the_run(
    test_db_engine: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One route failing to freeze must not stop other due routes from being
    frozen and credited in the same run."""
    maker = _maker(test_db_engine)
    monkeypatch.setattr(driver_history_jobs, "async_session_maker_instance", maker)

    poisoned = await _seed(maker, drive_date=date.today() - timedelta(days=1))
    healthy = await _seed(maker)

    async with maker() as s:
        s.add(
            DriverHistory(
                driver_id=poisoned["driver_id"],
                route_id=poisoned["route_id"],
                drive_date=date.today() - timedelta(days=1),
                km=1.0,
                kind=MileageEntryKindEnum.AUTO,
            )
        )
        await s.commit()

    await driver_history_jobs.process_daily_driver_history()

    async with maker() as s:
        snaps = (await s.execute(select(RouteSnapshot))).scalars().all()
        assert len(snaps) == 1
        assert snaps[0].route_id == healthy["route_id"]

        healthy_entries = (
            (
                await s.execute(
                    select(DriverHistory).where(
                        DriverHistory.route_id == healthy["route_id"]
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(healthy_entries) == 1
        assert healthy_entries[0].km == pytest.approx(ROUTE_KM)

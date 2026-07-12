"""Tests for derived driver mileage.

The invariant under test throughout: a driver's km is always
SUM(route.length) over their FROZEN routes (those with a RouteSnapshot),
bucketed by the group's drive_date month, plus their signed manual
adjustments. There is no stored total — so reassignment, route edits, date
corrections, and deletions all update history automatically and can never
drift.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.driver import Driver
from app.models.location import Location
from app.models.location_group import LocationGroup
from app.models.route import Route, RoutePatchRequest
from app.models.route_group import RouteGroup, RouteGroupUpdate
from app.models.route_snapshot import RouteSnapshot
from app.models.route_stop import RouteStop
from app.models.route_stop_snapshot import RouteStopSnapshot
from app.models.system_settings import SystemSettings
from app.models.user import User
from app.services.implementations.driver_history_service import DriverHistoryService
from app.services.implementations.location_service import (
    LocationInUseError,
    LocationService,
)
from app.services.implementations.route_group_service import RouteGroupService
from app.services.implementations.route_service import RouteService

logger = logging.getLogger(__name__)

FROZEN_KM = 52.0

history_service = DriverHistoryService(logger)


async def _lifetime(session: AsyncSession, driver_id: UUID) -> float:
    summary = await history_service.get_driver_history_summary(session, driver_id)
    return summary.lifetime_km


async def _make_driver(session: AsyncSession, tag: str) -> Driver:
    user = User(
        first_name=tag.capitalize(),
        last_name="Driver",
        email=f"{tag}@test.dev",
        auth_id=f"auth-{tag}",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    driver = Driver(
        user_id=user.user_id,
        phone="+12125551234",
        address="1 Depot Rd",
        license_plate=tag.upper()[:6],
        car_make_model="Toyota Corolla",
        active=True,
    )
    session.add(driver)
    await session.commit()
    await session.refresh(driver)
    return driver


@pytest_asyncio.fixture
async def frozen_world(test_session: AsyncSession) -> dict[str, Any]:
    """A frozen route (yesterday, driver A, length FROZEN_KM) plus a spare
    driver B, an UN-frozen future route for A, and two geocoded locations."""
    driver_a = await _make_driver(test_session, "alice")
    driver_b = await _make_driver(test_session, "bob")

    # Set warehouse coords on the existing settings row if another fixture
    # (e.g. async_client) already created one; otherwise create it.
    existing_settings = (
        (await test_session.execute(select(SystemSettings))).scalars().first()
    )
    if existing_settings is None:
        test_session.add(
            SystemSettings(
                warehouse_location="Warehouse",
                warehouse_latitude=43.0,
                warehouse_longitude=-80.0,
            )
        )
    else:
        existing_settings.warehouse_location = "Warehouse"
        existing_settings.warehouse_latitude = 43.0
        existing_settings.warehouse_longitude = -80.0
    group = LocationGroup(name="G", color="#fff", notes="")
    test_session.add(group)
    await test_session.commit()
    await test_session.refresh(group)

    locations = []
    for i in range(2):
        loc = Location(
            location_group_id=group.location_group_id,
            name=f"Fam{i}",
            contact_name=f"Fam{i}",
            address=f"{i} A St",
            phone_primary="+12125550001",
            latitude=43.1 + i * 0.01,
            longitude=-80.1 - i * 0.01,
            num_children=4,
            delivery_type="Family",
        )
        test_session.add(loc)
        locations.append(loc)
    await test_session.commit()
    for loc in locations:
        await test_session.refresh(loc)

    yesterday = date.today() - timedelta(days=1)
    rg = RouteGroup(
        name="Frozen group",
        drive_date=datetime.combine(yesterday, datetime.min.time()),
    )
    future_rg = RouteGroup(
        name="Future group",
        drive_date=datetime.combine(
            date.today() + timedelta(days=7), datetime.min.time()
        ),
    )
    test_session.add_all([rg, future_rg])
    await test_session.commit()
    await test_session.refresh(rg)
    await test_session.refresh(future_rg)

    route = Route(
        name="R-frozen",
        length=FROZEN_KM,
        route_group_id=rg.route_group_id,
        driver_id=driver_a.driver_id,
    )
    future_route = Route(
        name="R-future",
        length=99.0,
        route_group_id=future_rg.route_group_id,
        driver_id=driver_a.driver_id,
    )
    test_session.add_all([route, future_route])
    await test_session.commit()
    await test_session.refresh(route)
    await test_session.refresh(future_route)

    stop = RouteStop(
        route_id=route.route_id,
        location_id=locations[0].location_id,
        stop_number=1,
    )
    test_session.add(stop)
    await test_session.commit()
    await test_session.refresh(stop)

    # Freeze the past route: snapshot + stop snapshot, as the nightly job does.
    test_session.add(
        RouteSnapshot(
            route_id=route.route_id,
            start_address="Warehouse",
            start_latitude=43.0,
            start_longitude=-80.0,
        )
    )
    test_session.add(
        RouteStopSnapshot(
            route_stop_id=stop.route_stop_id,
            address=locations[0].address,
            contact_name=locations[0].contact_name,
            phone_primary=locations[0].phone_primary,
            phone_secondary=locations[0].phone_secondary,
            num_children=locations[0].num_children,
            notes=locations[0].notes,
            latitude=locations[0].latitude,
            longitude=locations[0].longitude,
        )
    )
    await test_session.commit()

    return {
        "driver_a": driver_a,
        "driver_b": driver_b,
        "route": route,
        "future_route": future_route,
        "route_group": rg,
        "locations": locations,
        "yesterday": yesterday,
    }


# ---------------------------------------------------------------------------
# Derived totals: what counts and what doesn't
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_only_frozen_routes_count(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    """The frozen route counts; the un-frozen future route (length 99) does
    not — freezing is what makes a route part of history."""
    a = frozen_world["driver_a"].driver_id
    assert await _lifetime(test_session, a) == pytest.approx(FROZEN_KM)


@pytest.mark.asyncio
async def test_driverless_frozen_route_counts_for_no_one(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    route = frozen_world["route"]
    route.driver_id = None
    await test_session.commit()

    a = frozen_world["driver_a"].driver_id
    b = frozen_world["driver_b"].driver_id
    assert await _lifetime(test_session, a) == pytest.approx(0.0)
    assert await _lifetime(test_session, b) == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_reassignment_just_works(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    """Reassigning a frozen route (even long after its drive date) moves the
    km — attribution IS the current assignment. This was the original bug:
    late assignments used to be silently uncredited."""
    service = RouteService(logger)
    a = frozen_world["driver_a"].driver_id
    b = frozen_world["driver_b"].driver_id

    await service.update_route(
        test_session,
        frozen_world["route"].route_id,
        RoutePatchRequest(driver_id=b),
    )

    assert await _lifetime(test_session, a) == pytest.approx(0.0)
    assert await _lifetime(test_session, b) == pytest.approx(FROZEN_KM)

    # Unassign → no one is credited.
    await service.update_route(
        test_session,
        frozen_world["route"].route_id,
        RoutePatchRequest(driver_id=None),
    )
    assert await _lifetime(test_session, b) == pytest.approx(0.0)

    # Late backfill-assign → credited retroactively.
    await service.update_route(
        test_session,
        frozen_world["route"].route_id,
        RoutePatchRequest(driver_id=a),
    )
    assert await _lifetime(test_session, a) == pytest.approx(FROZEN_KM)


@pytest.mark.asyncio
async def test_route_delete_removes_km(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    """Deleting a route removes its km — deletion means 'this never
    happened' (mistake correction), not archiving. Routes are kept forever
    otherwise; storage is trivial."""
    service = RouteService(logger)
    a = frozen_world["driver_a"].driver_id

    deleted = await service.delete_route(test_session, frozen_world["route"].route_id)
    assert deleted is True
    assert await _lifetime(test_session, a) == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_group_date_correction_rebuckets(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    """Fixing a group's drive_date moves its routes' km to the right month
    automatically — no guard needed, the derivation follows the data."""
    service = RouteGroupService(logger)
    a = frozen_world["driver_a"].driver_id
    yesterday = frozen_world["yesterday"]

    # Move the frozen group to a clearly different month.
    new_date = datetime(yesterday.year - 1, 3, 15)
    updated = await service.update_route_group(
        test_session,
        frozen_world["route_group"].route_group_id,
        RouteGroupUpdate(drive_date=new_date),
    )
    assert updated is not None

    monthly = await history_service.get_monthly_totals(test_session, a)
    by_bucket = {(t.year, t.month): t.km for t in monthly}
    assert by_bucket == {(new_date.year, 3): pytest.approx(FROZEN_KM)}


@pytest.mark.asyncio
async def test_frozen_stop_edit_updates_km_and_rebuilds_snapshots(
    test_session: AsyncSession,
    frozen_world: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Editing a frozen route's stops ('it was actually done this way')
    recomputes its length — which IS the driver's mileage — and rebuilds the
    per-stop snapshots instead of silently destroying them."""
    from app.services.implementations import route_service as route_service_module

    NEW_KM = 60.0

    async def fake_polyline(**_kwargs: Any) -> tuple[str, float]:
        return "fake-polyline", NEW_KM

    monkeypatch.setattr(route_service_module, "fetch_route_polyline", fake_polyline)

    service = RouteService(logger)
    a = frozen_world["driver_a"].driver_id
    locs = frozen_world["locations"]

    await service.update_route(
        test_session,
        frozen_world["route"].route_id,
        RoutePatchRequest(location_ids=[locs[1].location_id, locs[0].location_id]),
    )

    assert await _lifetime(test_session, a) == pytest.approx(NEW_KM)

    # Stop snapshots were rebuilt for the corrected stops (2 now), not
    # cascade-destroyed.
    stop_snaps = (await test_session.execute(select(RouteStopSnapshot))).scalars().all()
    assert len(stop_snaps) == 2
    snapped_addresses = {s.address for s in stop_snaps}
    assert snapped_addresses == {locs[0].address, locs[1].address}


@pytest.mark.asyncio
async def test_stop_edit_on_unfrozen_route_creates_no_snapshots(
    test_session: AsyncSession,
    frozen_world: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Editing an un-frozen route is planning, not record-correction: no
    stop snapshots are created (the nightly freeze will do that)."""
    from app.services.implementations import route_service as route_service_module

    async def fake_polyline(**_kwargs: Any) -> tuple[str, float]:
        return "fake-polyline", 42.0

    monkeypatch.setattr(route_service_module, "fetch_route_polyline", fake_polyline)

    service = RouteService(logger)
    locs = frozen_world["locations"]

    before = (await test_session.execute(select(RouteStopSnapshot))).scalars().all()
    await service.update_route(
        test_session,
        frozen_world["future_route"].route_id,
        RoutePatchRequest(location_ids=[locs[1].location_id]),
    )
    after = (await test_session.execute(select(RouteStopSnapshot))).scalars().all()
    assert len(after) == len(before)


# ---------------------------------------------------------------------------
# Adjustments: manual corrections compose with route-derived km
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_adjustments_compose_with_route_km(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    a = frozen_world["driver_a"].driver_id
    yesterday = frozen_world["yesterday"]

    # Same-month correction plus a different-month backfill.
    await history_service.create_adjustment(
        test_session, a, yesterday, -2.5, "over-credited"
    )
    other_month = (yesterday.replace(day=15) - timedelta(days=40)).replace(day=10)
    await history_service.create_adjustment(
        test_session, a, other_month, 7.0, "missed delivery"
    )

    monthly = await history_service.get_monthly_totals(test_session, a)
    by_bucket = {(t.year, t.month): t.km for t in monthly}
    assert by_bucket[(yesterday.year, yesterday.month)] == pytest.approx(
        FROZEN_KM - 2.5
    )
    assert by_bucket[(other_month.year, other_month.month)] == pytest.approx(7.0)

    summary = await history_service.get_driver_history_summary(test_session, a)
    assert summary.lifetime_km == pytest.approx(FROZEN_KM - 2.5 + 7.0)


@pytest.mark.asyncio
async def test_yearly_totals_sum_all_months(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    """The CSV export's yearly totals sum every month (the old code showed
    only the last month's km per driver)."""
    a = frozen_world["driver_a"].driver_id
    yesterday = frozen_world["yesterday"]

    # Add km in a second month of the same year (guaranteed same-year by
    # construction below).
    other_month_date = date(yesterday.year, 1 if yesterday.month != 1 else 2, 10)
    await history_service.create_adjustment(
        test_session, a, other_month_date, 10.0, "second month"
    )

    totals = await history_service.get_yearly_totals_by_driver(
        test_session, yesterday.year
    )
    assert totals[a] == pytest.approx(FROZEN_KM + 10.0)


# ---------------------------------------------------------------------------
# Driver delete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_driver_delete_endpoint_detaches_routes_and_km(
    async_client: Any, test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    """Deleting a driver removes the row; their frozen routes survive but
    become unattributed (driver_id SET NULL), so the km stop counting."""
    a = frozen_world["driver_a"]
    frozen_route = frozen_world["route"]

    resp = await async_client.delete(f"/drivers/{a.driver_id}")
    assert resp.status_code == 204

    gone = (
        (
            await test_session.execute(
                select(Driver).where(Driver.driver_id == a.driver_id)
            )
        )
        .scalars()
        .first()
    )
    assert gone is None
    # The route itself survives, unassigned.
    await test_session.refresh(frozen_route)
    assert frozen_route.driver_id is None
    assert await _lifetime(test_session, a.driver_id) == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_driver_delete_endpoint_404_when_missing(async_client: Any) -> None:
    resp = await async_client.delete("/drivers/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Location delete guard
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_location_delete_referenced_raises_in_use(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    service = LocationService(logger, None, None)  # type: ignore[arg-type]
    with pytest.raises(LocationInUseError, match="used by"):
        await service.delete_location_by_id(
            test_session, frozen_world["locations"][0].location_id
        )


@pytest.mark.asyncio
async def test_location_delete_unreferenced_succeeds(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    service = LocationService(logger, None, None)  # type: ignore[arg-type]
    # locations[1] is seeded but not on any route.
    await service.delete_location_by_id(
        test_session, frozen_world["locations"][1].location_id
    )
    remaining = (await test_session.execute(select(Location))).scalars().all()
    assert len(remaining) == 1


# ---------------------------------------------------------------------------
# API surface
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_history_api_monthly_view(
    async_client: Any, frozen_world: dict[str, Any]
) -> None:
    a = frozen_world["driver_a"].driver_id
    yesterday = frozen_world["yesterday"]

    monthly = await async_client.get(f"/drivers/{a}/history/")
    assert monthly.status_code == 200
    rows = monthly.json()
    assert len(rows) == 1
    assert rows[0]["year"] == yesterday.year
    assert rows[0]["month"] == yesterday.month
    assert rows[0]["km"] == pytest.approx(FROZEN_KM)

    month_without_year = await async_client.get(f"/drivers/{a}/history/?month=5")
    assert month_without_year.status_code == 400


@pytest.mark.asyncio
async def test_adjustment_api_roundtrip(
    async_client: Any, test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    a = frozen_world["driver_a"].driver_id

    created = await async_client.post(
        f"/drivers/{a}/history/adjustments",
        json={"drive_date": "2026-06-15", "km": -3.5, "note": "odometer check"},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["km"] == pytest.approx(-3.5)
    assert body["note"] == "odometer check"

    listing = await async_client.get(f"/drivers/{a}/history/adjustments")
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    assert await _lifetime(test_session, a) == pytest.approx(FROZEN_KM - 3.5)


@pytest.mark.asyncio
async def test_adjustment_api_validation(
    async_client: Any, frozen_world: dict[str, Any]
) -> None:
    a = frozen_world["driver_a"].driver_id

    no_note = await async_client.post(
        f"/drivers/{a}/history/adjustments",
        json={"drive_date": "2026-06-15", "km": 5.0, "note": ""},
    )
    assert no_note.status_code == 422  # min_length=1

    zero_km = await async_client.post(
        f"/drivers/{a}/history/adjustments",
        json={"drive_date": "2026-06-15", "km": 0, "note": "noop"},
    )
    assert zero_km.status_code == 400

    missing_driver = await async_client.post(
        "/drivers/00000000-0000-0000-0000-000000000000/history/adjustments",
        json={"drive_date": "2026-06-15", "km": 5.0, "note": "n"},
    )
    assert missing_driver.status_code == 404

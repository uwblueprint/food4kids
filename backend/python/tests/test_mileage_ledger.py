"""Tests for the driver mileage ledger: reconciliation hooks on frozen-route
edits, ledger arithmetic (totals as sums over entries), deletion survival,
manual adjustments, and the editing guards.

The ledger invariant under test throughout: a driver's total km always equals
the sum of their entries, and the driver currently assigned to a frozen route
nets exactly that route's credited length — no matter what sequence of
reassignments, amendments, or deletions got us there.
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
from app.models.driver_history import DriverHistory
from app.models.enum import MileageEntryKindEnum
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
from app.services.implementations.location_service import LocationInUseError
from app.services.implementations.route_group_service import RouteGroupService
from app.services.implementations.route_service import RouteService

logger = logging.getLogger(__name__)

FROZEN_KM = 52.0


async def _driver_total(session: AsyncSession, driver_id: UUID) -> float:
    entries = (
        (
            await session.execute(
                select(DriverHistory).where(DriverHistory.driver_id == driver_id)
            )
        )
        .scalars()
        .all()
    )
    return sum(e.km for e in entries)


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
    """A frozen route (yesterday, credited to driver A via an AUTO entry,
    snapshot.length_km == FROZEN_KM) plus a spare driver B and two geocoded
    locations — the starting state for reconciliation tests."""
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
    test_session.add(rg)
    await test_session.commit()
    await test_session.refresh(rg)

    route = Route(
        name="R-frozen",
        length=FROZEN_KM,
        route_group_id=rg.route_group_id,
        driver_id=driver_a.driver_id,
    )
    test_session.add(route)
    await test_session.commit()
    await test_session.refresh(route)

    stop = RouteStop(
        route_id=route.route_id,
        location_id=locations[0].location_id,
        stop_number=1,
    )
    test_session.add(stop)
    await test_session.commit()
    await test_session.refresh(stop)

    # Freeze: snapshot + stop snapshot + AUTO credit, as the nightly job does.
    test_session.add(
        RouteSnapshot(
            route_id=route.route_id,
            start_address="Warehouse",
            start_latitude=43.0,
            start_longitude=-80.0,
            length_km=FROZEN_KM,
        )
    )
    test_session.add(
        RouteStopSnapshot(
            route_stop_id=stop.route_stop_id,
            address=locations[0].address,
            contact_name=locations[0].contact_name,
            phone_number=locations[0].phone_primary,
            num_children=locations[0].num_children,
            notes=locations[0].notes,
            latitude=locations[0].latitude,
            longitude=locations[0].longitude,
        )
    )
    test_session.add(
        DriverHistory(
            driver_id=driver_a.driver_id,
            route_id=route.route_id,
            drive_date=yesterday,
            km=FROZEN_KM,
            kind=MileageEntryKindEnum.AUTO,
        )
    )
    await test_session.commit()

    return {
        "driver_a": driver_a,
        "driver_b": driver_b,
        "route": route,
        "route_group": rg,
        "locations": locations,
        "yesterday": yesterday,
    }


# ---------------------------------------------------------------------------
# Reassignment matrix on FROZEN routes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_frozen_reassign_a_to_b_moves_credit(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    service = RouteService(logger)
    a = frozen_world["driver_a"].driver_id
    b = frozen_world["driver_b"].driver_id

    await service.update_route(
        test_session,
        frozen_world["route"].route_id,
        RoutePatchRequest(driver_id=b),
    )

    assert await _driver_total(test_session, a) == pytest.approx(0.0)
    assert await _driver_total(test_session, b) == pytest.approx(FROZEN_KM)

    # The moves are explicit compensating entries, not edits.
    entries = (await test_session.execute(select(DriverHistory))).scalars().all()
    kinds = sorted(e.kind for e in entries)
    assert kinds == [
        MileageEntryKindEnum.AUTO,
        MileageEntryKindEnum.REASSIGNMENT,
        MileageEntryKindEnum.REASSIGNMENT,
    ]
    # Reassignment entries are bucketed under the route's drive_date.
    for e in entries:
        assert e.drive_date == frozen_world["yesterday"]


@pytest.mark.asyncio
async def test_frozen_unassign_reverses_credit(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    service = RouteService(logger)
    a = frozen_world["driver_a"].driver_id

    await service.update_route(
        test_session,
        frozen_world["route"].route_id,
        RoutePatchRequest(driver_id=None),
    )

    assert await _driver_total(test_session, a) == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_frozen_backfill_assign_credits_late_driver(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    """A3, the original bug: assigning a driver to a route AFTER it froze
    (e.g. it was driverless on its drive date) credits them retroactively."""
    service = RouteService(logger)
    a = frozen_world["driver_a"].driver_id
    b = frozen_world["driver_b"].driver_id

    # Unassign (A net 0), then later backfill-assign B.
    await service.update_route(
        test_session,
        frozen_world["route"].route_id,
        RoutePatchRequest(driver_id=None),
    )
    await service.update_route(
        test_session,
        frozen_world["route"].route_id,
        RoutePatchRequest(driver_id=b),
    )

    assert await _driver_total(test_session, a) == pytest.approx(0.0)
    assert await _driver_total(test_session, b) == pytest.approx(FROZEN_KM)


@pytest.mark.asyncio
async def test_unfrozen_reassign_posts_no_entries(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    """Reassigning an UN-frozen (future) route is pure planning — the ledger
    only moves for frozen routes; the eventual AUTO credit follows whoever
    is assigned at freeze time."""
    service = RouteService(logger)
    b = frozen_world["driver_b"].driver_id

    tomorrow_group = RouteGroup(
        name="Future group",
        drive_date=datetime.combine(
            date.today() + timedelta(days=1), datetime.min.time()
        ),
    )
    test_session.add(tomorrow_group)
    await test_session.commit()
    await test_session.refresh(tomorrow_group)
    future_route = Route(
        name="R-future",
        length=99.0,
        route_group_id=tomorrow_group.route_group_id,
        driver_id=frozen_world["driver_a"].driver_id,
    )
    test_session.add(future_route)
    await test_session.commit()
    await test_session.refresh(future_route)

    before = (await test_session.execute(select(DriverHistory))).scalars().all()
    await service.update_route(
        test_session, future_route.route_id, RoutePatchRequest(driver_id=b)
    )
    after = (await test_session.execute(select(DriverHistory))).scalars().all()
    assert len(after) == len(before)


# ---------------------------------------------------------------------------
# Frozen-route amendment (stop edits)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_frozen_stop_edit_amends_snapshots_and_posts_delta(
    test_session: AsyncSession,
    frozen_world: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Editing stops on a frozen route ('it was actually done this way')
    rebuilds the stop snapshots, updates the frozen credited length, and
    posts the km delta to the assigned driver."""
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

    # Driver A nets exactly the corrected length.
    assert await _driver_total(test_session, a) == pytest.approx(NEW_KM)

    # The delta is an explicit, explained adjustment entry.
    adjustments = (
        (
            await test_session.execute(
                select(DriverHistory).where(
                    DriverHistory.kind == MileageEntryKindEnum.MANUAL_ADJUSTMENT
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(adjustments) == 1
    assert adjustments[0].km == pytest.approx(NEW_KM - FROZEN_KM)
    assert "amended" in adjustments[0].note

    # The frozen record tracks the correction.
    snap = (await test_session.execute(select(RouteSnapshot))).scalars().one()
    assert snap.length_km == pytest.approx(NEW_KM)

    # Stop snapshots were rebuilt for the corrected stops (2 now), not
    # cascade-destroyed.
    stop_snaps = (await test_session.execute(select(RouteStopSnapshot))).scalars().all()
    assert len(stop_snaps) == 2


@pytest.mark.asyncio
async def test_frozen_combined_reassign_and_amend_nets_new_length(
    test_session: AsyncSession,
    frozen_world: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One PATCH that both reassigns A→B and corrects the stops: B must net
    exactly the corrected length, A exactly zero."""
    from app.services.implementations import route_service as route_service_module

    NEW_KM = 61.5

    async def fake_polyline(**_kwargs: Any) -> tuple[str, float]:
        return "fake-polyline", NEW_KM

    monkeypatch.setattr(route_service_module, "fetch_route_polyline", fake_polyline)

    service = RouteService(logger)
    a = frozen_world["driver_a"].driver_id
    b = frozen_world["driver_b"].driver_id
    locs = frozen_world["locations"]

    await service.update_route(
        test_session,
        frozen_world["route"].route_id,
        RoutePatchRequest(
            driver_id=b,
            location_ids=[locs[0].location_id, locs[1].location_id],
        ),
    )

    assert await _driver_total(test_session, a) == pytest.approx(0.0)
    assert await _driver_total(test_session, b) == pytest.approx(NEW_KM)


# ---------------------------------------------------------------------------
# Deletion survival: mileage is a historical fact
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_route_delete_keeps_mileage(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    service = RouteService(logger)
    a = frozen_world["driver_a"].driver_id

    deleted = await service.delete_route(test_session, frozen_world["route"].route_id)
    assert deleted is True

    # The credit survives; it just loses its route pointer.
    assert await _driver_total(test_session, a) == pytest.approx(FROZEN_KM)
    entry = (await test_session.execute(select(DriverHistory))).scalars().one()
    assert entry.route_id is None
    assert entry.driver_id == a


@pytest.mark.asyncio
async def test_route_group_delete_keeps_mileage(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    service = RouteGroupService(logger)
    a = frozen_world["driver_a"].driver_id

    deleted = await service.delete_route_group(
        test_session, frozen_world["route_group"].route_group_id
    )
    assert deleted is True

    assert await _driver_total(test_session, a) == pytest.approx(FROZEN_KM)


@pytest.mark.asyncio
async def test_hard_driver_delete_orphans_but_keeps_entries(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    """Belt-and-braces FK check: even a HARD driver delete (not exposed via
    the API anymore) must not destroy ledger rows — driver_id nulls out."""
    driver_a = frozen_world["driver_a"]

    await test_session.delete(driver_a)
    await test_session.commit()

    entry = (await test_session.execute(select(DriverHistory))).scalars().one()
    assert entry.driver_id is None
    assert entry.km == pytest.approx(FROZEN_KM)


# ---------------------------------------------------------------------------
# Driver soft-delete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_driver_delete_endpoint_deactivates(
    async_client: Any, test_session: AsyncSession
) -> None:
    driver = await _make_driver(test_session, "carol")

    resp = await async_client.delete(f"/drivers/{driver.driver_id}")
    assert resp.status_code == 204

    survivor = (
        (
            await test_session.execute(
                select(Driver).where(Driver.driver_id == driver.driver_id)
            )
        )
        .scalars()
        .first()
    )
    assert survivor is not None
    assert survivor.active is False


@pytest.mark.asyncio
async def test_driver_delete_endpoint_404_when_missing(
    async_client: Any,
) -> None:
    resp = await async_client.delete("/drivers/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_drive_date_move_rejected_on_frozen_group(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    service = RouteGroupService(logger)
    with pytest.raises(ValueError, match="frozen"):
        await service.update_route_group(
            test_session,
            frozen_world["route_group"].route_group_id,
            RouteGroupUpdate(drive_date=datetime(2026, 12, 25)),
        )


@pytest.mark.asyncio
async def test_drive_date_move_allowed_on_unfrozen_group(
    test_session: AsyncSession,
) -> None:
    service = RouteGroupService(logger)
    rg = RouteGroup(name="Unfrozen", drive_date=datetime(2026, 8, 1))
    test_session.add(rg)
    await test_session.commit()
    await test_session.refresh(rg)

    updated = await service.update_route_group(
        test_session,
        rg.route_group_id,
        RouteGroupUpdate(drive_date=datetime(2026, 8, 8)),
    )
    assert updated is not None
    assert updated.drive_date == datetime(2026, 8, 8)


@pytest.mark.asyncio
async def test_location_delete_referenced_raises_in_use(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    from app.services.implementations.location_service import LocationService

    service = LocationService(logger, None, None)  # type: ignore[arg-type]
    with pytest.raises(LocationInUseError, match="used by"):
        await service.delete_location_by_id(
            test_session, frozen_world["locations"][0].location_id
        )


@pytest.mark.asyncio
async def test_location_delete_unreferenced_succeeds(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    from app.services.implementations.location_service import LocationService

    service = LocationService(logger, None, None)  # type: ignore[arg-type]
    # locations[1] is seeded but not on any route.
    await service.delete_location_by_id(
        test_session, frozen_world["locations"][1].location_id
    )
    remaining = (await test_session.execute(select(Location))).scalars().all()
    assert len(remaining) == 1


# ---------------------------------------------------------------------------
# Ledger arithmetic: totals & manual adjustments (service + API)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_monthly_totals_bucket_by_drive_date(
    test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    """Entries land in the month the delivery HAPPENED (drive_date), and
    signed entries in the same bucket sum."""
    service = DriverHistoryService(logger)
    a = frozen_world["driver_a"].driver_id
    yesterday = frozen_world["yesterday"]

    # A correction in the same month, plus an entry in a different month.
    await service.create_adjustment(test_session, a, yesterday, -2.5, "over-credited")
    other_month = (yesterday.replace(day=15) - timedelta(days=40)).replace(day=10)
    await service.create_adjustment(
        test_session, a, other_month, 7.0, "missed delivery"
    )

    totals = await service.get_monthly_totals(test_session, a)
    by_bucket = {(t.year, t.month): t.km for t in totals}
    assert by_bucket[(yesterday.year, yesterday.month)] == pytest.approx(
        FROZEN_KM - 2.5
    )
    assert by_bucket[(other_month.year, other_month.month)] == pytest.approx(7.0)

    summary = await service.get_driver_history_summary(test_session, a)
    assert summary.lifetime_km == pytest.approx(FROZEN_KM - 2.5 + 7.0)


@pytest.mark.asyncio
async def test_adjustment_api_posts_entry(
    async_client: Any, test_session: AsyncSession, frozen_world: dict[str, Any]
) -> None:
    a = frozen_world["driver_a"].driver_id

    resp = await async_client.post(
        f"/drivers/{a}/history/adjustments",
        json={"drive_date": "2026-06-15", "km": -3.5, "note": "odometer check"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["km"] == pytest.approx(-3.5)
    assert body["kind"] == "manual_adjustment"
    assert body["note"] == "odometer check"

    assert await _driver_total(test_session, a) == pytest.approx(FROZEN_KM - 3.5)


@pytest.mark.asyncio
async def test_adjustment_api_requires_note_and_nonzero_km(
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


@pytest.mark.asyncio
async def test_history_api_monthly_and_entries_views(
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

    entries = await async_client.get(f"/drivers/{a}/history/entries")
    assert entries.status_code == 200
    entry_rows = entries.json()
    assert len(entry_rows) == 1
    assert entry_rows[0]["kind"] == "auto"
    assert entry_rows[0]["km"] == pytest.approx(FROZEN_KM)

    month_without_year = await async_client.get(f"/drivers/{a}/history/?month=5")
    assert month_without_year.status_code == 400

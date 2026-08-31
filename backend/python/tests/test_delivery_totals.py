"""Tests for report delivery totals.

A delivery is one stop on one drive date — a route_stop_snapshots row on a
frozen route. The invariants under test:

* the all-time total is all time, not the trailing window the homepage charts;
* the org's totals count every frozen route, including routes with no driver.
  `Route.driver_id` is nulled when a driver is deleted, so a total that skipped
  NULL rows would shed a departed volunteer's whole history — and volunteers
  come and go. NULL is excluded only where a driver is the unit being reported:
  the Top Drivers ranking and the per-driver CSV export;
* every drive_date range in the reports is half-open [start, end), so the 1st
  of the next month belongs to the next month.
"""

import logging
from datetime import date, datetime, time
from unittest.mock import patch
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver
from app.models.location import Location
from app.models.location_group import LocationGroup
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_snapshot import RouteSnapshot
from app.models.route_stop import RouteStop
from app.models.route_stop_snapshot import RouteStopSnapshot
from app.models.user import User
from app.services.implementations.driver_history_service import (
    DriverHistoryService,
    month_bounds,
)
from app.services.implementations.driver_report_service import DriverReportService
from app.utilities.datetime_utils import from_local_wall_clock

logger = logging.getLogger(__name__)
service = DriverReportService(logger)

KM_PER_ROUTE = 10.0


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


async def _make_locations(session: AsyncSession, count: int) -> list[Location]:
    group = LocationGroup(name="G", color="#fff", notes="")
    session.add(group)
    await session.commit()
    await session.refresh(group)

    locations = [
        Location(
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
        for i in range(count)
    ]
    session.add_all(locations)
    await session.commit()
    for location in locations:
        await session.refresh(location)
    return locations


async def _add_route(
    session: AsyncSession,
    drive_date: date,
    locations: list[Location],
    driver_id: UUID | None,
    *,
    frozen: bool = True,
    km: float = KM_PER_ROUTE,
) -> Route:
    """One route on `drive_date` with a stop per location.

    Frozen means snapshotted, exactly as the nightly freeze job leaves it: a
    RouteSnapshot plus a RouteStopSnapshot per stop. Only frozen stops are
    deliveries.
    """
    route_group = RouteGroup(name=f"G {drive_date.isoformat()}", drive_date=drive_date)
    session.add(route_group)
    await session.commit()
    await session.refresh(route_group)

    route = Route(
        name=f"R {drive_date.isoformat()}",
        length=km,
        route_group_id=route_group.route_group_id,
        driver_id=driver_id,
        # An assigned route must carry a start time (DB check constraint).
        start_time=time(8, 0) if driver_id is not None else None,
    )
    session.add(route)
    await session.commit()
    await session.refresh(route)

    stops = [
        RouteStop(
            route_id=route.route_id,
            location_id=location.location_id,
            stop_number=index + 1,
        )
        for index, location in enumerate(locations)
    ]
    session.add_all(stops)
    await session.commit()
    for stop in stops:
        await session.refresh(stop)

    if not frozen:
        return route

    session.add(
        RouteSnapshot(
            route_id=route.route_id,
            start_address="Warehouse",
            start_latitude=43.0,
            start_longitude=-80.0,
        )
    )
    for stop, location in zip(stops, locations, strict=True):
        session.add(
            RouteStopSnapshot(
                route_stop_id=stop.route_stop_id,
                address=location.address,
                contact_name=location.contact_name,
                phone_primary=location.phone_primary,
                phone_secondary=location.phone_secondary,
                num_children=location.num_children,
                latitude=location.latitude,
                longitude=location.longitude,
            )
        )
    await session.commit()
    return route


# ---------------------------------------------------------------------------
# All time means all time
# ---------------------------------------------------------------------------

# Deliberately longer than the six months the homepage charts: a windowed sum
# masquerading as a total only shows up once history outruns the window.
HISTORY_MONTHS = 14
STOPS_PER_ROUTE = 2
ANCHOR = (2026, 6)


@pytest_asyncio.fixture
async def long_history(test_session: AsyncSession) -> Driver:
    """One frozen, driven route on the 15th of each of the 14 months ending
    at ANCHOR, two stops apiece."""
    driver = await _make_driver(test_session, "alice")
    locations = await _make_locations(test_session, STOPS_PER_ROUTE)

    anchor_ordinal = ANCHOR[0] * 12 + (ANCHOR[1] - 1)
    for ordinal in range(anchor_ordinal - (HISTORY_MONTHS - 1), anchor_ordinal + 1):
        await _add_route(
            test_session,
            date(ordinal // 12, ordinal % 12 + 1, 15),
            locations,
            driver.driver_id,
        )
    return driver


@pytest.mark.usefixtures("long_history")
@pytest.mark.asyncio
async def test_all_time_total_counts_every_month_of_history(
    test_session: AsyncSession,
) -> None:
    total = await service.get_total_deliveries(test_session)
    assert total == HISTORY_MONTHS * STOPS_PER_ROUTE


@pytest.mark.usefixtures("long_history")
@pytest.mark.asyncio
async def test_all_time_total_is_not_the_six_month_window(
    test_session: AsyncSession,
) -> None:
    series = await service.get_monthly_series(test_session, *ANCHOR, 6)
    windowed = sum(point["total_deliveries"] for point in series)

    assert windowed == 6 * STOPS_PER_ROUTE
    assert await service.get_total_deliveries(test_session) > windowed


@pytest.mark.usefixtures("long_history")
@pytest.mark.asyncio
async def test_all_time_km_covers_the_same_history(
    test_session: AsyncSession,
) -> None:
    assert await service.get_total_km(test_session) == HISTORY_MONTHS * KM_PER_ROUTE


@pytest.mark.asyncio
async def test_all_time_totals_are_zero_on_an_empty_database(
    test_session: AsyncSession,
) -> None:
    assert await service.get_total_deliveries(test_session) == 0
    assert await service.get_total_km(test_session) == 0.0


@pytest.mark.usefixtures("long_history")
@pytest.mark.asyncio
async def test_all_time_endpoint_returns_both_totals(
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/reports/totals")

    assert response.status_code == 200
    assert response.json() == {
        "total_km": HISTORY_MONTHS * KM_PER_ROUTE,
        "total_deliveries": HISTORY_MONTHS * STOPS_PER_ROUTE,
    }


# ---------------------------------------------------------------------------
# Routes with no driver still count for the org
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_driverless_routes_count_towards_deliveries_and_km(
    test_session: AsyncSession,
) -> None:
    driver = await _make_driver(test_session, "bob")
    locations = await _make_locations(test_session, 3)
    drive_date = date(2026, 4, 15)

    await _add_route(test_session, drive_date, locations[:2], driver.driver_id)
    # Frozen, three stops, no driver_id — either never assigned, or assigned
    # to someone since deleted. The org drove it either way.
    await _add_route(test_session, drive_date, locations, None)

    bounds = month_bounds(drive_date.year, drive_date.month)
    assert await service.get_total_deliveries(test_session) == 5
    assert await service.get_total_deliveries(test_session, bounds) == 5
    assert await service.get_total_km(test_session) == 2 * KM_PER_ROUTE

    series = await service.get_monthly_series(test_session, 2026, 4, 1)
    assert series[0]["total_deliveries"] == 5
    assert series[0]["total_km"] == 2 * KM_PER_ROUTE


@pytest.mark.asyncio
async def test_driverless_routes_are_absent_from_the_top_drivers_ranking(
    test_session: AsyncSession,
) -> None:
    """The org counts the route; the ranking has nobody to credit for it."""
    driver = await _make_driver(test_session, "frank")
    locations = await _make_locations(test_session, 2)
    drive_date = date(2026, 4, 15)

    await _add_route(test_session, drive_date, locations, driver.driver_id)
    await _add_route(test_session, drive_date, locations, None)

    ranking = await service.get_monthly_km_ranking(test_session, 2026, 4)

    assert [row["driver_id"] for row in ranking] == [str(driver.driver_id)]
    assert ranking[0]["km"] == KM_PER_ROUTE
    # The driverless route is in the org total but in nobody's row.
    assert await service.get_total_km(test_session) == 2 * KM_PER_ROUTE


@pytest.mark.asyncio
async def test_driverless_routes_are_absent_from_the_per_driver_export(
    test_session: AsyncSession,
) -> None:
    """The yearly CSV export is keyed by driver, so a NULL key is meaningless."""
    history_service = DriverHistoryService(logger)
    driver = await _make_driver(test_session, "grace")
    locations = await _make_locations(test_session, 1)

    await _add_route(test_session, date(2026, 4, 15), locations, driver.driver_id)
    await _add_route(test_session, date(2026, 5, 15), locations, None)

    totals = await history_service.get_yearly_totals_by_driver(test_session, 2026)

    assert totals == {driver.driver_id: KM_PER_ROUTE}
    assert None not in totals


@pytest.mark.asyncio
async def test_deleting_a_driver_leaves_the_org_totals_unchanged(
    async_client: AsyncClient, test_session: AsyncSession
) -> None:
    """The scenario this guards: ordinary volunteer churn.

    Driver delete is a hard delete that nulls `Route.driver_id`, so a total
    that counted only routes with a driver would drop everything the departed
    volunteer ever delivered — silently, and for good.
    """
    driver = await _make_driver(test_session, "heidi")
    locations = await _make_locations(test_session, 3)
    await _add_route(test_session, date(2026, 4, 15), locations, driver.driver_id)
    await _add_route(test_session, date(2026, 5, 15), locations, driver.driver_id)

    before = await async_client.get("/reports/totals")
    assert before.json() == {"total_km": 2 * KM_PER_ROUTE, "total_deliveries": 6}

    with patch("firebase_admin.auth.delete_user"):
        deleted = await async_client.delete(f"/drivers/{driver.driver_id}")
    assert deleted.status_code == 204, deleted.text

    after = await async_client.get("/reports/totals")
    assert after.json() == before.json()

    # ...but the routes really are unattributed now, so nobody is ranked.
    assert await service.get_monthly_km_ranking(test_session, 2026, 4) == []


@pytest.mark.asyncio
async def test_unfrozen_routes_are_not_deliveries(test_session: AsyncSession) -> None:
    driver = await _make_driver(test_session, "carol")
    locations = await _make_locations(test_session, 2)

    await _add_route(
        test_session, date(2026, 4, 15), locations, driver.driver_id, frozen=False
    )

    assert await service.get_total_deliveries(test_session) == 0


# ---------------------------------------------------------------------------
# Month boundaries are half-open
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def boundary_history(test_session: AsyncSession) -> Driver:
    """One single-stop delivery on each of four dates straddling two month
    boundaries: Mar 31, Apr 1, Apr 30, May 1."""
    driver = await _make_driver(test_session, "dave")
    locations = await _make_locations(test_session, 1)

    for drive_date in (
        date(2026, 3, 31),
        date(2026, 4, 1),
        date(2026, 4, 30),
        date(2026, 5, 1),
    ):
        await _add_route(test_session, drive_date, locations, driver.driver_id)
    return driver


@pytest.mark.usefixtures("boundary_history")
@pytest.mark.asyncio
async def test_monthly_totals_exclude_the_first_of_the_next_month(
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/reports/monthly/2026/4/totals")

    assert response.status_code == 200
    # Apr 1 and Apr 30 — not May 1, and not Mar 31.
    assert response.json()["total_deliveries"] == 2
    assert response.json()["total_km"] == 2 * KM_PER_ROUTE


@pytest.mark.usefixtures("boundary_history")
@pytest.mark.asyncio
async def test_monthly_totals_include_the_first_of_their_own_month(
    async_client: AsyncClient,
) -> None:
    march = await async_client.get("/reports/monthly/2026/3/totals")
    may = await async_client.get("/reports/monthly/2026/5/totals")

    assert march.json()["total_deliveries"] == 1
    assert may.json()["total_deliveries"] == 1


@pytest.mark.asyncio
async def test_december_rolls_into_the_next_year_not_month_thirteen(
    test_session: AsyncSession,
) -> None:
    driver = await _make_driver(test_session, "erin")
    locations = await _make_locations(test_session, 1)
    await _add_route(test_session, date(2026, 12, 31), locations, driver.driver_id)
    await _add_route(test_session, date(2027, 1, 1), locations, driver.driver_id)

    december = await service.get_total_deliveries(test_session, month_bounds(2026, 12))
    january = await service.get_total_deliveries(test_session, month_bounds(2027, 1))

    assert (december, january) == (1, 1)


@pytest.mark.usefixtures("boundary_history")
@pytest.mark.asyncio
async def test_consecutive_month_totals_tile_without_double_counting(
    test_session: AsyncSession,
) -> None:
    months = [(2026, 3), (2026, 4), (2026, 5)]
    per_month = [
        await service.get_total_deliveries(test_session, month_bounds(year, month))
        for year, month in months
    ]

    assert sum(per_month) == await service.get_total_deliveries(test_session)


@pytest.mark.usefixtures("boundary_history")
@pytest.mark.asyncio
async def test_deliveries_count_range_is_half_open(
    async_client: AsyncClient,
) -> None:
    response = await async_client.get(
        "/reports/deliveries/count",
        params={"start": "2026-04-01T00:00:00", "end": "2026-05-01T00:00:00"},
    )

    assert response.status_code == 200
    assert response.json() == {"total_deliveries": 2}


@pytest.mark.usefixtures("boundary_history")
@pytest.mark.asyncio
async def test_deliveries_count_reads_naive_bounds_as_local_time(
    async_client: AsyncClient,
) -> None:
    """The end bound is a wall-clock time in F4K's zone, not UTC.

    Midnight local on May 1 is 04:00 UTC — read as UTC it would still be
    Apr 30 locally, pulling that day out of the window.
    """
    naive = await async_client.get(
        "/reports/deliveries/count",
        params={"start": "2026-04-01T00:00:00", "end": "2026-05-01T00:00:00"},
    )
    explicit = await async_client.get(
        "/reports/deliveries/count",
        params={
            # The same two wall-clock instants, sent as explicit UTC offsets.
            "start": from_local_wall_clock(datetime(2026, 4, 1, 0, 0)).isoformat(),
            "end": from_local_wall_clock(datetime(2026, 5, 1, 0, 0)).isoformat(),
        },
    )

    assert naive.json() == explicit.json() == {"total_deliveries": 2}


# ---------------------------------------------------------------------------
# The series' default window is anchored in F4K's timezone
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_default_series_window_follows_local_month_not_utc(
    async_client: AsyncClient,
) -> None:
    """Late on Aug 31 in Waterloo it is already Sep 1 in UTC; the newest bar
    must still be August."""
    late_august = from_local_wall_clock(datetime(2026, 8, 31, 23, 30))
    assert late_august.month == 9  # the trap: UTC has already rolled over

    with patch("app.routers.report_routes.now_utc", return_value=late_august):
        response = await async_client.get(
            "/reports/monthly-series", params={"months": 6}
        )

    assert response.status_code == 200
    newest = response.json()[-1]
    assert (newest["year"], newest["month"]) == (2026, 8)

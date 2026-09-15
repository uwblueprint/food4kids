"""Driver table aggregates must agree with history and sort before pagination."""

import logging
from datetime import date, datetime, time, timezone
from typing import Any
from unittest.mock import patch
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_snapshot import RouteSnapshot
from app.models.user import User
from app.services.implementations.driver_history_service import DriverHistoryService


class NewYearClock(datetime):
    @classmethod
    def now(cls, tz: Any = None) -> datetime:
        # UTC has reached 2027; Toronto is still in 2026.
        instant = datetime(2027, 1, 1, 2, tzinfo=timezone.utc)
        return instant.astimezone(tz) if tz else instant.replace(tzinfo=None)


@pytest.fixture(autouse=True)
def local_new_year() -> Any:
    with (
        patch("app.services.implementations.driver_service.datetime", NewYearClock),
        patch(
            "app.services.implementations.driver_history_service.datetime", NewYearClock
        ),
        patch(
            "app.routers.driver_routes.driver_service.timezone",
            ZoneInfo("America/Toronto"),
        ),
    ):
        yield


async def add_route(
    session: AsyncSession,
    driver_id: UUID,
    drive_date: date,
    km: float,
    frozen: bool = True,
) -> None:
    group = RouteGroup(name="Mileage group", drive_date=drive_date)
    session.add(group)
    await session.flush()
    route = Route(
        name="Mileage route",
        route_group_id=group.route_group_id,
        driver_id=driver_id,
        start_time=time(8),
        length=km,
    )
    session.add(route)
    await session.flush()
    if frozen:
        session.add(
            RouteSnapshot(
                route_id=route.route_id,
                start_address="Warehouse",
                start_latitude=43.0,
                start_longitude=-80.0,
            )
        )
    await session.flush()


@pytest_asyncio.fixture
async def drivers(test_session: AsyncSession) -> dict[str, Driver]:
    drivers = {}
    for name in ("Alpha", "Bravo", "Charlie"):
        user = User(
            first_name=name, last_name="Driver", email=f"{name}@test.dev", auth_id=None
        )
        test_session.add(user)
        await test_session.flush()
        driver = Driver(user_id=user.user_id)
        test_session.add(driver)
        await test_session.flush()
        drivers[name] = driver

    alpha = drivers["Alpha"].driver_id
    bravo = drivers["Bravo"].driver_id
    await add_route(test_session, alpha, date(2026, 1, 1), 10)
    await add_route(test_session, alpha, date(2026, 12, 30), 2.5)
    await add_route(test_session, alpha, date(2025, 12, 31), 20)
    await add_route(test_session, alpha, date(2024, 12, 31), 100)
    # A future-year snapshot must not inflate this year's mileage.
    await add_route(test_session, alpha, date(2027, 1, 1), 900)
    await add_route(test_session, alpha, date(2027, 1, 2), 700, frozen=False)
    await add_route(test_session, alpha, date(2026, 12, 31), 600, frozen=False)
    await add_route(test_session, bravo, date(2026, 6, 1), 30)
    await add_route(test_session, bravo, date(2025, 1, 1), 5)
    await test_session.commit()
    return drivers


@pytest.mark.asyncio
async def test_driver_list_aggregates_match_history_at_local_new_year(
    async_client: AsyncClient,
    test_session: AsyncSession,
    drivers: dict[str, Driver],
) -> None:
    response = await async_client.get("/drivers/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    rows = {row["first_name"]: row for row in data["items"]}
    alpha = rows["Alpha"]
    assert alpha["current_year_km"] == 12.5
    assert alpha["last_year_km"] == 20
    assert alpha["last_delivery"] == "2027-01-01"
    assert alpha["is_active"] is True
    assert rows["Bravo"]["last_delivery"] == "2026-06-01"
    assert rows["Bravo"]["is_active"] is False
    assert rows["Charlie"]["current_year_km"] == 0
    assert rows["Charlie"]["last_year_km"] == 0
    assert rows["Charlie"]["last_delivery"] is None
    assert rows["Charlie"]["is_active"] is False

    history = DriverHistoryService(logging.getLogger(__name__))
    history.timezone = ZoneInfo("America/Toronto")
    for name, driver in drivers.items():
        summary = await history.get_driver_history_summary(
            test_session, driver.driver_id
        )
        assert rows[name]["current_year_km"] == summary.current_year_km
        assert rows[name]["last_year_km"] == summary.last_year_km


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("sort_by", "order", "expected"),
    [
        ("name", "asc", ["Alpha", "Bravo", "Charlie"]),
        ("name", "desc", ["Charlie", "Bravo", "Alpha"]),
        ("current_year_km", "asc", ["Charlie", "Alpha", "Bravo"]),
        ("current_year_km", "desc", ["Bravo", "Alpha", "Charlie"]),
        ("last_year_km", "asc", ["Charlie", "Bravo", "Alpha"]),
        ("last_year_km", "desc", ["Alpha", "Bravo", "Charlie"]),
        ("last_delivery", "asc", ["Bravo", "Alpha", "Charlie"]),
        ("last_delivery", "desc", ["Alpha", "Bravo", "Charlie"]),
    ],
)
async def test_driver_list_sorts_before_pagination(
    async_client: AsyncClient,
    drivers: dict[str, Driver],
    sort_by: str,
    order: str,
    expected: list[str],
) -> None:
    assert len(drivers) == 3
    names = []
    for page in (1, 2, 3):
        response = await async_client.get(
            "/drivers/",
            params={"sort_by": sort_by, "order": order, "page": page, "page_size": 1},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["total_pages"] == 3
        names.append(data["items"][0]["first_name"])
    assert names == expected

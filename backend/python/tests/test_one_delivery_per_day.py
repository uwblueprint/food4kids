"""A family gets one delivery a day.

Editing a route's stops, duplicating a route group, and moving a group to a new
date are all refused when they would put a family on a second route on the
same drive date. Routes on other dates don't count.
"""

import logging
from datetime import date, timedelta
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location
from app.models.location_group import LocationGroup
from app.models.route import Route, RoutePatchRequest
from app.models.route_group import RouteGroup, RouteGroupDuplicate, RouteGroupUpdate
from app.models.route_stop import RouteStop
from app.models.system_settings import SystemSettings
from app.services.implementations import route_service as route_service_module
from app.services.implementations.route_group_service import RouteGroupService
from app.services.implementations.route_service import RouteService
from app.utilities.datetime_utils import today_local

logger = logging.getLogger(__name__)
route_service = RouteService(logger)
group_service = RouteGroupService(logger)


async def _route(
    session: AsyncSession, drive_date: date, locations: list[Location], name: str
) -> Route:
    group = RouteGroup(name=f"G {name}", drive_date=drive_date)
    session.add(group)
    await session.commit()
    await session.refresh(group)
    route = Route(name=name, length=1.0, route_group_id=group.route_group_id)
    session.add(route)
    await session.commit()
    await session.refresh(route)
    for i, loc in enumerate(locations, start=1):
        session.add(
            RouteStop(
                route_id=route.route_id, location_id=loc.location_id, stop_number=i
            )
        )
    await session.commit()
    return route


@pytest_asyncio.fixture
async def world(
    test_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Any]:
    """Routes A and B on the same future day (in different groups), route C the
    next day, each with its own family, plus a fourth family on no route."""

    async def fake_polyline(**_kwargs: Any) -> tuple[str, float]:
        return "fake-polyline", 5.0

    monkeypatch.setattr(route_service_module, "fetch_route_polyline", fake_polyline)

    test_session.add(
        SystemSettings(
            warehouse_location="Warehouse",
            warehouse_latitude=43.0,
            warehouse_longitude=-80.0,
        )
    )
    group = LocationGroup(name="LG", color="#fff", notes="")
    test_session.add(group)
    await test_session.commit()
    await test_session.refresh(group)

    locations = []
    for i in range(4):
        loc = Location(
            location_group_id=group.location_group_id,
            name=f"Fam{i}",
            contact_name=f"Fam{i}",
            address=f"{i} A St",
            phone_primary="+12125550001",
            latitude=43.1 + i * 0.01,
            longitude=-80.1 - i * 0.01,
            num_children=2,
            delivery_type="Family",
        )
        test_session.add(loc)
        locations.append(loc)
    await test_session.commit()
    for loc in locations:
        await test_session.refresh(loc)

    day = today_local() + timedelta(days=7)
    return {
        "day": day,
        "locations": locations,
        "route_a": await _route(test_session, day, [locations[0]], "Route A"),
        "route_b": await _route(test_session, day, [locations[1]], "Route B"),
        "route_c": await _route(
            test_session, day + timedelta(days=1), [locations[2]], "Route C"
        ),
    }


# Editing a route's stops (Add Stop / Move Stop)


@pytest.mark.asyncio
async def test_edit_rejects_family_already_on_another_route_that_day(
    test_session: AsyncSession, world: dict[str, Any]
) -> None:
    locs = world["locations"]
    with pytest.raises(ValueError, match="already on another route that day"):
        await route_service.update_route(
            test_session,
            world["route_a"].route_id,
            RoutePatchRequest(location_ids=[locs[0].location_id, locs[1].location_id]),
        )


@pytest.mark.asyncio
async def test_edit_allows_family_on_a_route_another_day(
    test_session: AsyncSession, world: dict[str, Any]
) -> None:
    locs = world["locations"]
    route = await route_service.update_route(
        test_session,
        world["route_a"].route_id,
        RoutePatchRequest(location_ids=[locs[0].location_id, locs[2].location_id]),
    )
    assert route is not None


@pytest.mark.asyncio
async def test_existing_double_booking_does_not_block_other_edits(
    test_session: AsyncSession, world: dict[str, Any]
) -> None:
    locs = world["locations"]
    route_a = world["route_a"]
    # Route B's family also on Route A, as left over from before this check.
    test_session.add(
        RouteStop(
            route_id=route_a.route_id, location_id=locs[1].location_id, stop_number=2
        )
    )
    await test_session.commit()

    # Adding an unrelated family still works...
    route = await route_service.update_route(
        test_session,
        route_a.route_id,
        RoutePatchRequest(
            location_ids=[
                locs[0].location_id,
                locs[1].location_id,
                locs[3].location_id,
            ]
        ),
    )
    assert route is not None

    # ...but adding a family that's routed elsewhere that day is still refused.
    with pytest.raises(ValueError, match="already on another route that day"):
        await route_service.update_route(
            test_session,
            world["route_b"].route_id,
            RoutePatchRequest(location_ids=[locs[1].location_id, locs[0].location_id]),
        )


@pytest.mark.asyncio
async def test_edit_rejects_the_same_family_twice(
    test_session: AsyncSession, world: dict[str, Any]
) -> None:
    loc = world["locations"][0]
    with pytest.raises(ValueError, match="only appear once"):
        await route_service.update_route(
            test_session,
            world["route_a"].route_id,
            RoutePatchRequest(location_ids=[loc.location_id, loc.location_id]),
        )


@pytest.mark.asyncio
async def test_edit_api_returns_400(async_client: Any, world: dict[str, Any]) -> None:
    locs = world["locations"]
    resp = await async_client.patch(
        f"/routes/{world['route_a'].route_id}",
        json={"location_ids": [str(locs[0].location_id), str(locs[1].location_id)]},
    )
    assert resp.status_code == 400


# Duplicating a route group


@pytest.mark.asyncio
async def test_duplicate_onto_the_same_day_is_rejected(
    test_session: AsyncSession, world: dict[str, Any]
) -> None:
    with pytest.raises(ValueError, match="already on a route"):
        await group_service.duplicate_route_group(
            test_session, world["route_a"].route_group_id
        )


@pytest.mark.asyncio
async def test_duplicate_onto_a_free_day_works(
    test_session: AsyncSession, world: dict[str, Any]
) -> None:
    copy = await group_service.duplicate_route_group(
        test_session,
        world["route_a"].route_group_id,
        RouteGroupDuplicate(drive_date=world["day"] + timedelta(days=14)),
    )
    assert copy is not None


@pytest.mark.asyncio
async def test_duplicate_api_returns_400(
    async_client: Any, world: dict[str, Any]
) -> None:
    resp = await async_client.post(
        f"/route-groups/{world['route_a'].route_group_id}/duplicate",
        json={"drive_date": world["day"].isoformat()},
    )
    assert resp.status_code == 400


# Moving a route group to another date


@pytest.mark.asyncio
async def test_moving_onto_a_day_where_its_families_are_routed_is_rejected(
    test_session: AsyncSession, world: dict[str, Any]
) -> None:
    # Route C's family is put on Route A's day too, then C is moved onto it.
    locs = world["locations"]
    await route_service.update_route(
        test_session,
        world["route_a"].route_id,
        RoutePatchRequest(location_ids=[locs[0].location_id, locs[2].location_id]),
    )
    with pytest.raises(ValueError, match="already on a route"):
        await group_service.update_route_group(
            test_session,
            world["route_c"].route_group_id,
            RouteGroupUpdate(drive_date=world["day"]),
        )


@pytest.mark.asyncio
async def test_moving_onto_a_day_with_other_families_works(
    test_session: AsyncSession, world: dict[str, Any]
) -> None:
    moved = await group_service.update_route_group(
        test_session,
        world["route_c"].route_group_id,
        RouteGroupUpdate(drive_date=world["day"]),
    )
    assert moved is not None
    assert moved.drive_date == world["day"]

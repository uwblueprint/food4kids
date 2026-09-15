"""The assigned-route invariant: driver_id set implies start_time set.

An assigned route is a scheduled route -- the driver has to be told when to
show up. Enforced twice on purpose: a CHECK constraint so no write path can
get around it, and a service-layer check so a client sees a 400 instead of the
database raising a 500 at them.
"""

from datetime import time, timedelta
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver
from app.models.route import (
    ASSIGNED_ROUTE_HAS_START_TIME_CONSTRAINT,
    Route,
    RoutePatchRequest,
)
from app.models.route_group import RouteGroup
from app.models.user import User
from app.services.implementations.route_service import RouteService
from app.utilities.datetime_utils import today_local


async def _make_driver(session: AsyncSession) -> Driver:
    user = User(
        first_name="Assigned",
        last_name="Driver",
        email=f"driver-{uuid4().hex[:8]}@test.dev",
        auth_id=f"uid-{uuid4().hex[:8]}",
    )
    driver = Driver(
        user_id=user.user_id,
        phone="+12125551234",
        address="1 Depot Rd",
        license_plate="DRV1",
        car_make_model="Toyota Corolla",
    )
    session.add_all([user, driver])
    await session.commit()
    await session.refresh(driver)
    return driver


async def _make_route_group(session: AsyncSession) -> RouteGroup:
    group = RouteGroup(
        name=f"Group {uuid4().hex[:6]}",
        drive_date=today_local() + timedelta(days=1),
    )
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return group


# --------------------------------------------------------------------------
# Database constraint
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_constraint_rejects_assigned_route_without_start_time(
    test_session: AsyncSession,
) -> None:
    """The database refuses an assigned route that has no start time."""
    driver = await _make_driver(test_session)
    group = await _make_route_group(test_session)

    test_session.add(
        Route(
            name="R1",
            length=10.0,
            route_group_id=group.route_group_id,
            driver_id=driver.driver_id,
            start_time=None,
        )
    )

    with pytest.raises(IntegrityError) as excinfo:
        await test_session.commit()
    assert ASSIGNED_ROUTE_HAS_START_TIME_CONSTRAINT in str(excinfo.value)
    await test_session.rollback()


@pytest.mark.asyncio
async def test_constraint_allows_unassigned_route_without_start_time(
    test_session: AsyncSession,
) -> None:
    """An unscheduled, unassigned route is still legal."""
    group = await _make_route_group(test_session)

    test_session.add(
        Route(
            name="R-unassigned",
            length=10.0,
            route_group_id=group.route_group_id,
            driver_id=None,
            start_time=None,
        )
    )
    await test_session.commit()  # must not raise


@pytest.mark.asyncio
async def test_constraint_allows_unassigned_route_with_start_time(
    test_session: AsyncSession,
) -> None:
    """A route may be scheduled before anyone is assigned to it."""
    group = await _make_route_group(test_session)

    test_session.add(
        Route(
            name="R-scheduled",
            length=10.0,
            route_group_id=group.route_group_id,
            driver_id=None,
            start_time=time(8, 0),
        )
    )
    await test_session.commit()  # must not raise


@pytest.mark.asyncio
async def test_constraint_allows_assigned_route_with_start_time(
    test_session: AsyncSession,
) -> None:
    """The ordinary case still works."""
    driver = await _make_driver(test_session)
    group = await _make_route_group(test_session)

    test_session.add(
        Route(
            name="R-ok",
            length=10.0,
            route_group_id=group.route_group_id,
            driver_id=driver.driver_id,
            start_time=time(8, 15),
        )
    )
    await test_session.commit()  # must not raise


# --------------------------------------------------------------------------
# Service-layer validation (so clients get a 400, not a 500)
# --------------------------------------------------------------------------


async def _route(
    session: AsyncSession, *, driver: Driver | None, start_time: time | None
) -> Route:
    group = await _make_route_group(session)
    route = Route(
        name="R",
        length=10.0,
        route_group_id=group.route_group_id,
        driver_id=driver.driver_id if driver else None,
        start_time=start_time,
    )
    session.add(route)
    await session.commit()
    await session.refresh(route)
    return route


@pytest.mark.asyncio
async def test_patch_rejects_assigning_driver_without_start_time(
    test_session: AsyncSession,
) -> None:
    """Assigning a driver to an unscheduled route is a client error."""
    driver = await _make_driver(test_session)
    route = await _route(test_session, driver=None, start_time=None)

    with pytest.raises(ValueError, match="must have a start_time"):
        await RouteService(logger=_logger()).update_route(
            test_session, route.route_id, RoutePatchRequest(driver_id=driver.driver_id)
        )


@pytest.mark.asyncio
async def test_patch_rejects_clearing_start_time_of_assigned_route(
    test_session: AsyncSession,
) -> None:
    """Unscheduling a route without unassigning it is a client error."""
    driver = await _make_driver(test_session)
    route = await _route(test_session, driver=driver, start_time=time(8, 0))

    with pytest.raises(ValueError, match="must have a start_time"):
        await RouteService(logger=_logger()).update_route(
            test_session, route.route_id, RoutePatchRequest(start_time=None)
        )


@pytest.mark.asyncio
async def test_patch_allows_assigning_driver_and_start_time_together(
    test_session: AsyncSession,
) -> None:
    """The two fields travel together, which is the supported way to schedule."""
    driver = await _make_driver(test_session)
    route = await _route(test_session, driver=None, start_time=None)

    updated = await RouteService(logger=_logger()).update_route(
        test_session,
        route.route_id,
        RoutePatchRequest(driver_id=driver.driver_id, start_time=time(8, 30)),
    )

    assert updated is not None
    assert updated.driver_id == driver.driver_id
    assert updated.start_time == time(8, 30)


@pytest.mark.asyncio
async def test_patch_allows_unassigning_and_clearing_together(
    test_session: AsyncSession,
) -> None:
    """Clearing both at once returns the route to unassigned + unscheduled."""
    driver = await _make_driver(test_session)
    route = await _route(test_session, driver=driver, start_time=time(8, 0))

    updated = await RouteService(logger=_logger()).update_route(
        test_session,
        route.route_id,
        RoutePatchRequest(driver_id=None, start_time=None),
    )

    assert updated is not None
    assert updated.driver_id is None
    assert updated.start_time is None


@pytest.mark.asyncio
async def test_patch_allows_unassigning_while_keeping_start_time(
    test_session: AsyncSession,
) -> None:
    """A route may keep its schedule after the driver drops off it."""
    driver = await _make_driver(test_session)
    route = await _route(test_session, driver=driver, start_time=time(8, 0))

    updated = await RouteService(logger=_logger()).update_route(
        test_session, route.route_id, RoutePatchRequest(driver_id=None)
    )

    assert updated is not None
    assert updated.driver_id is None
    assert updated.start_time == time(8, 0)


@pytest.mark.asyncio
async def test_patch_unrelated_field_on_assigned_route_still_works(
    test_session: AsyncSession,
) -> None:
    """The check reads merged state, so it must not fire on an untouched route."""
    driver = await _make_driver(test_session)
    route = await _route(test_session, driver=driver, start_time=time(8, 0))

    updated = await RouteService(logger=_logger()).update_route(
        test_session, route.route_id, RoutePatchRequest(name="Renamed")
    )

    assert updated is not None
    assert updated.name == "Renamed"
    assert updated.start_time == time(8, 0)


def _logger() -> Any:
    import logging

    return logging.getLogger("test-route-service")

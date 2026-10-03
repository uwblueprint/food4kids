"""Routes API usage recorded by route edits.

Re-ordering a route's stops fetches a fresh polyline, which spends the same
Routes API allowance the single-vehicle generation tier gates on. The counter
has to reflect every call Google was paid for, including the ones that came
back an error: under-reporting is what lets the cascade offer a tier room it
no longer has, and sail into paid usage.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlmodel import select

from app.models.location import Location
from app.models.location_group import LocationGroup
from app.models.route import Route, RoutePatchRequest
from app.models.route_group import RouteGroup
from app.models.route_stop import RouteStop
from app.models.system_settings import SystemSettings
from app.services.implementations import route_service as route_service_module
from app.services.implementations.route_service import RouteService
from app.utilities.datetime_utils import today_local

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def editable_route(test_session: AsyncSession) -> dict[str, Any]:
    """A route with two geocoded stops, and a warehouse to route from."""
    existing = (await test_session.execute(select(SystemSettings))).scalars().first()
    if existing is None:
        test_session.add(
            SystemSettings(
                warehouse_location="Warehouse",
                warehouse_latitude=43.0,
                warehouse_longitude=-80.0,
            )
        )
    else:
        existing.warehouse_latitude = 43.0
        existing.warehouse_longitude = -80.0

    group = LocationGroup(name="G", color="#fff", notes="")
    test_session.add(group)
    await test_session.commit()
    await test_session.refresh(group)

    locations = []
    for i in range(2):
        location = Location(
            location_group_id=group.location_group_id,
            name=f"Fam{i}",
            contact_name=f"Fam{i}",
            address=f"{i} A St",
            phone_primary="tel:+1-519-576-0000",
            latitude=43.1 + i * 0.01,
            longitude=-80.1 - i * 0.01,
            num_children=4,
            delivery_type="Family",
        )
        test_session.add(location)
        locations.append(location)
    await test_session.commit()
    for location in locations:
        await test_session.refresh(location)

    route_group = RouteGroup(name="Edit group", drive_date=today_local())
    test_session.add(route_group)
    await test_session.commit()
    await test_session.refresh(route_group)

    route = Route(
        name="R-edit",
        length=10.0,
        route_group_id=route_group.route_group_id,
    )
    test_session.add(route)
    await test_session.commit()
    await test_session.refresh(route)

    test_session.add(
        RouteStop(
            route_id=route.route_id,
            location_id=locations[0].location_id,
            stop_number=1,
        )
    )
    await test_session.commit()

    return {"route": route, "locations": locations}


def _capture_usage(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    recorded: list[int] = []

    async def _record(_sku: Any, units: int) -> None:
        recorded.append(units)

    monkeypatch.setattr(route_service_module, "record_usage_out_of_band", _record)
    return recorded


async def _reorder(session: AsyncSession, world: dict[str, Any]) -> None:
    locations = world["locations"]
    await RouteService(logger).update_route(
        session,
        world["route"].route_id,
        RoutePatchRequest(
            location_ids=[
                locations[1].location_id,
                locations[0].location_id,
            ]
        ),
    )


class TestRouteEditUsage:
    async def test_a_successful_reroute_is_counted(
        self,
        test_session: AsyncSession,
        editable_route: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        async def _polyline(**_kwargs: Any) -> tuple[str, float]:
            return "fake-polyline", 42.0

        monkeypatch.setattr(route_service_module, "fetch_route_polyline", _polyline)
        recorded = _capture_usage(monkeypatch)

        await _reorder(test_session, editable_route)

        assert recorded == [1]

    async def test_a_failed_reroute_still_counts_the_billed_call(
        self,
        test_session: AsyncSession,
        editable_route: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """fetch_route_polyline raises HTTPException only after the request
        reached Google, so that call was billed and has to be counted."""

        async def _unavailable(**_kwargs: Any) -> tuple[str, float]:
            raise HTTPException(status_code=503, detail="Google Maps API error")

        monkeypatch.setattr(route_service_module, "fetch_route_polyline", _unavailable)
        recorded = _capture_usage(monkeypatch)

        with pytest.raises(HTTPException):
            await _reorder(test_session, editable_route)

        assert recorded == [1]

    async def test_a_reroute_that_was_never_sent_is_not_counted(
        self,
        test_session: AsyncSession,
        editable_route: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """ValueError is the one failure raised before anything is sent, so
        a misconfigured key must not inflate the counter on every edit."""

        async def _unsent(**_kwargs: Any) -> tuple[str, float]:
            raise ValueError("Google Maps API key is not configured in settings")

        monkeypatch.setattr(route_service_module, "fetch_route_polyline", _unsent)
        recorded = _capture_usage(monkeypatch)

        with pytest.raises(ValueError, match="not configured"):
            await _reorder(test_session, editable_route)

        assert sum(recorded) == 0

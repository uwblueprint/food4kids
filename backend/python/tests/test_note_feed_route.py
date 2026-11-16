import logging
from datetime import date
from typing import Any

import pytest

from app.models.location import Location
from app.models.location_group import LocationGroup
from app.models.note import Note
from app.models.note_chain import NoteChain
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_stop import RouteStop
from app.schemas.pagination import PaginationParams
from app.services.implementations.note_chain_service import NoteChainService


@pytest.mark.asyncio
async def test_feed_route_is_nullable_and_uses_latest_drive_date(
    test_session: Any,
) -> None:
    session = test_session
    group = LocationGroup(name="Schools")
    chain = NoteChain(read_permission="All", write_permission="All")
    session.add_all([group, chain])
    await session.flush()
    location = Location(
        location_group_id=group.location_group_id,
        note_chain_id=chain.note_chain_id,
        name="School",
        contact_name="Contact",
        address="123 Main St",
        phone_primary="+14165551234",
        delivery_type="School",
    )
    session.add_all(
        [location, Note(note_chain_id=chain.note_chain_id, message="Side entrance")]
    )
    await session.flush()
    service = NoteChainService(logging.getLogger(__name__))
    page = await service.get_location_notes_feed(session, PaginationParams())
    assert page.total == 1
    assert page.items[0].route_id is None

    latest = None
    # Insert the older drive date last to catch ordering by insertion time.
    for drive_date in [date(2026, 11, 20), date(2026, 11, 10)]:
        route_group = RouteGroup(name=str(drive_date), drive_date=drive_date)
        session.add(route_group)
        await session.flush()
        route = Route(name="Route", length=1, route_group_id=route_group.route_group_id)
        session.add(route)
        await session.flush()
        session.add(
            RouteStop(
                route_id=route.route_id, location_id=location.location_id, stop_number=1
            )
        )
        if latest is None:
            latest = route.route_id
    await session.flush()
    page = await service.get_location_notes_feed(
        session, PaginationParams(page=1, page_size=1)
    )
    assert page.total == 1
    assert len(page.items) == 1
    assert page.items[0].route_id == latest

from uuid import uuid4

import pytest

from app.models.location import Location
from app.utilities.routes_utils import fetch_route_polyline


@pytest.mark.asyncio
async def test_fetch_route_polyline_with_return():
    """Test fetching polyline with return to warehouse."""

    # Create mock locations
    loc1 = Location(
        location_group_id=uuid4(),
        contact_name="Test 1 Loc 1",
        address="123 Test St",
        phone_number="123-456-7890",
        longitude=-80.50,
        latitude=43.45,
        halal=True,
        dietary_restrictions="",
        num_boxes=5,
        notes="",
    )

    loc2 = Location(
        location_group_id=uuid4(),
        contact_name="Test 1 Loc 2",
        address="124 Test St",
        phone_number="124-456-7890",
        longitude=-80.51,
        latitude=43.46,
        halal=True,
        dietary_restrictions="",
        num_boxes=5,
        notes="",
    )

    polyline, distance_km = await fetch_route_polyline(
        locations=[loc1, loc2],
        warehouse_lat=43.40,
        warehouse_lon=-80.46,
        ends_at_warehouse=True,
    )

    assert isinstance(polyline, str)
    assert distance_km > 0.0
    assert len(polyline) > 0
    print(f"Encoded Polyline: {polyline}")

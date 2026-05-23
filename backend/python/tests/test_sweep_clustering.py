"""Tests for SweepClusteringAlgorithm."""

from __future__ import annotations

import math
from uuid import uuid4

import pytest

from app.models.location import Location
from app.services.implementations.sweep_clustering import (
    DEFAULT_MAX_BOXES_PER_CLUSTER,
    FAR_MAX_STOPS_PER_CLUSTER,
    SweepClusteringAlgorithm,
    effective_boxes,
)


def _location(
    *,
    lat: float,
    lon: float,
    num_children: int | None = None,
    num_boxes: int = 0,
    address: str = "123 Main St, Kitchener, ON",
    name: str = "Test School",
) -> Location:
    return Location(
        location_id=uuid4(),
        contact_name=name,
        address=address,
        phone_number="5195550100",
        latitude=lat,
        longitude=lon,
        num_children=num_children,
        num_boxes=num_boxes,
    )


WAREHOUSE_LAT = 43.4516
WAREHOUSE_LON = -80.4925


@pytest.mark.parametrize(
    ("num_children", "num_boxes", "expected"),
    [
        (5, 0, 3),
        (6, 0, 3),
        (1, 10, 1),
        (None, 4, 4),
        (0, 2, 2),
    ],
)
def test_effective_boxes_ceil_half_children(
    num_children: int | None, num_boxes: int, expected: int
) -> None:
    loc = _location(lat=0.0, lon=0.0, num_children=num_children, num_boxes=num_boxes)
    assert effective_boxes(loc) == expected


@pytest.mark.asyncio
async def test_cluster_locations_returns_exactly_num_drivers() -> None:
    algo = SweepClusteringAlgorithm(WAREHOUSE_LAT, WAREHOUSE_LON)
    locations = [
        _location(lat=43.46 + i * 0.01, lon=-80.49, num_children=2)
        for i in range(12)
    ]
    num_drivers = 4
    clusters = await algo.cluster_locations(
        locations=locations,
        num_clusters=num_drivers,
        max_boxes_per_cluster=14,
        max_locations_per_cluster=10,
    )
    assert len(clusters) == num_drivers
    assert sum(len(c) for c in clusters) == len(locations)


@pytest.mark.asyncio
async def test_max_boxes_per_cluster_defaults_to_14() -> None:
    algo = SweepClusteringAlgorithm(WAREHOUSE_LAT, WAREHOUSE_LON)
    # 29 children -> ceil(29/2) = 15 boxes, above default cap of 14
    locations = [_location(lat=43.46, lon=-80.49, num_children=29)]
    with pytest.raises(ValueError, match="exceeds the per-driver maximum of 14"):
        await algo.cluster_locations(locations=locations, num_clusters=1)


@pytest.mark.asyncio
async def test_each_cluster_respects_box_cap() -> None:
    algo = SweepClusteringAlgorithm(WAREHOUSE_LAT, WAREHOUSE_LON)
    locations = [
        _location(lat=43.46 + i * 0.008, lon=-80.49 - i * 0.005, num_children=4)
        for i in range(10)
    ]
    clusters = await algo.cluster_locations(
        locations=locations,
        num_clusters=3,
        max_boxes_per_cluster=DEFAULT_MAX_BOXES_PER_CLUSTER,
    )
    for cluster in clusters:
        assert sum(effective_boxes(loc) for loc in cluster) <= 14


@pytest.mark.asyncio
async def test_far_address_limits_stops_per_route() -> None:
    algo = SweepClusteringAlgorithm(WAREHOUSE_LAT, WAREHOUSE_LON)
    near = [
        _location(lat=43.46, lon=-80.49, num_children=2, address="1 King St, Kitchener")
        for _ in range(6)
    ]
    far = [
        _location(
            lat=43.60,
            lon=-80.70,
            num_children=2,
            address="10 Main St, Elmira, ON",
        )
        for _ in range(4)
    ]
    clusters = await algo.cluster_locations(
        locations=near + far,
        num_clusters=3,
        max_boxes_per_cluster=14,
        max_locations_per_cluster=12,
    )
    for cluster in clusters:
        has_far = any("elmira" in loc.address.lower() for loc in cluster)
        if has_far:
            assert len(cluster) <= FAR_MAX_STOPS_PER_CLUSTER


@pytest.mark.asyncio
async def test_load_spread_across_drivers() -> None:
    algo = SweepClusteringAlgorithm(WAREHOUSE_LAT, WAREHOUSE_LON)
    locations = [
        _location(lat=43.45 + i * 0.01, lon=-80.50, num_children=2)
        for i in range(8)
    ]
    clusters = await algo.cluster_locations(
        locations=locations,
        num_clusters=4,
        max_boxes_per_cluster=14,
    )
    sizes = [len(c) for c in clusters]
    assert max(sizes) - min(sizes) <= 1

"""Tests for SweepClusteringAlgorithm."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.models.enum import DeliveryTypeEnum
from app.models.location import Location
from app.services.implementations.sweep_clustering import (
    DEFAULT_MAX_BOXES_PER_CLUSTER,
    FAR_DISTANCE_KM_THRESHOLD,
    FAR_MAX_STOPS_PER_CLUSTER,
    SweepClusteringAlgorithm,
    effective_boxes,
)


def _location(
    *,
    lat: float,
    lon: float,
    num_children: int = 0,
    address: str = "123 Main St, Kitchener, ON",
    name: str = "Test School",
) -> Location:
    return Location(
        location_id=uuid4(),
        location_group_id=uuid4(),
        name=name,
        contact_name=name,
        delivery_type=DeliveryTypeEnum.SCHOOL,
        address=address,
        phone_primary="5195550100",
        latitude=lat,
        longitude=lon,
        num_children=num_children,
    )


WAREHOUSE_LAT = 43.4516
WAREHOUSE_LON = -80.4925
# Boxes are derived as ceil(num_children / children_per_box); 2 children per box.
CHILDREN_PER_BOX = 2


@pytest.mark.parametrize(
    ("num_children", "children_per_box", "expected"),
    [
        (5, 2, 3),  # ceil(5/2)
        (6, 2, 3),
        (1, 2, 1),
        (0, 2, 0),
        (10, 3, 4),  # ceil(10/3)
        (4, 1, 4),
    ],
)
def test_effective_boxes_ceil_children_per_box(
    num_children: int, children_per_box: int, expected: int
) -> None:
    loc = _location(lat=0.0, lon=0.0, num_children=num_children)
    assert effective_boxes(loc, children_per_box) == expected


@pytest.mark.asyncio
async def test_cluster_locations_returns_exactly_num_drivers() -> None:
    algo = SweepClusteringAlgorithm(WAREHOUSE_LAT, WAREHOUSE_LON, CHILDREN_PER_BOX)
    locations = [
        _location(lat=43.46 + i * 0.01, lon=-80.49, num_children=2) for i in range(12)
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
    algo = SweepClusteringAlgorithm(WAREHOUSE_LAT, WAREHOUSE_LON, CHILDREN_PER_BOX)
    # 29 children -> ceil(29/2) = 15 boxes, above default cap of 14
    locations = [_location(lat=43.46, lon=-80.49, num_children=29)]
    with pytest.raises(ValueError, match="exceeds the per-driver maximum of 14"):
        await algo.cluster_locations(locations=locations, num_clusters=1)


@pytest.mark.asyncio
async def test_each_cluster_respects_box_cap() -> None:
    algo = SweepClusteringAlgorithm(WAREHOUSE_LAT, WAREHOUSE_LON, CHILDREN_PER_BOX)
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
        assert sum(effective_boxes(loc, CHILDREN_PER_BOX) for loc in cluster) <= 14


@pytest.mark.asyncio
async def test_far_address_limits_stops_per_route() -> None:
    algo = SweepClusteringAlgorithm(WAREHOUSE_LAT, WAREHOUSE_LON, CHILDREN_PER_BOX)
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
    algo = SweepClusteringAlgorithm(WAREHOUSE_LAT, WAREHOUSE_LON, CHILDREN_PER_BOX)
    locations = [
        _location(lat=43.45 + i * 0.01, lon=-80.50, num_children=2) for i in range(8)
    ]
    clusters = await algo.cluster_locations(
        locations=locations,
        num_clusters=4,
        max_boxes_per_cluster=14,
    )
    sizes = [len(c) for c in clusters]
    assert max(sizes) - min(sizes) <= 1


@pytest.mark.asyncio
async def test_far_route_caps_at_five_stops_when_max_stops_omitted() -> None:
    """Far routes use FAR_MAX_STOPS_PER_CLUSTER even without max_locations_per_cluster."""
    algo = SweepClusteringAlgorithm(WAREHOUSE_LAT, WAREHOUSE_LON, CHILDREN_PER_BOX)
    far = [
        _location(
            lat=43.60,
            lon=-80.70,
            num_children=2,
            address="10 Main St, Elmira, ON",
        )
        for _ in range(6)
    ]
    clusters = await algo.cluster_locations(
        locations=far,
        num_clusters=2,
        max_boxes_per_cluster=14,
    )
    for cluster in clusters:
        assert len(cluster) <= FAR_MAX_STOPS_PER_CLUSTER


@pytest.mark.asyncio
async def test_far_by_haversine_distance_limits_stops() -> None:
    """Locations beyond FAR_DISTANCE_KM_THRESHOLD are far without a city keyword."""
    algo = SweepClusteringAlgorithm(WAREHOUSE_LAT, WAREHOUSE_LON, CHILDREN_PER_BOX)
    # ~55 km north of warehouse; address has no far-city keyword.
    distant = [
        _location(
            lat=44.0,
            lon=-80.4925,
            num_children=2,
            address="100 Rural Road, Fergus, ON",
        )
        for _ in range(4)
    ]
    metrics = algo._location_metrics(distant[0])
    assert metrics.distance_km >= FAR_DISTANCE_KM_THRESHOLD
    assert metrics.is_far

    # Long drive time limits how many far stops fit per route; use one driver per stop.
    clusters = await algo.cluster_locations(
        locations=distant,
        num_clusters=len(distant),
        max_boxes_per_cluster=14,
    )
    for cluster in clusters:
        assert len(cluster) <= FAR_MAX_STOPS_PER_CLUSTER


@pytest.mark.asyncio
async def test_cluster_locations_by_constraints_flushes_on_box_cap() -> None:
    algo = SweepClusteringAlgorithm(WAREHOUSE_LAT, WAREHOUSE_LON, CHILDREN_PER_BOX)
    # 4 boxes each (8 children); cap 14 -> at most 3 stops per cluster -> multiple clusters.
    locations = [
        _location(lat=43.46 + i * 0.005, lon=-80.49, num_children=8) for i in range(7)
    ]
    clusters = await algo.cluster_locations_by_constraints(
        locations=locations,
        max_boxes_per_cluster=14,
    )
    assert len(clusters) >= 2
    assert sum(len(c) for c in clusters) == len(locations)
    for cluster in clusters:
        assert sum(effective_boxes(loc, CHILDREN_PER_BOX) for loc in cluster) <= 14


@pytest.mark.asyncio
async def test_cluster_locations_by_constraints_rejects_oversized_location() -> None:
    algo = SweepClusteringAlgorithm(WAREHOUSE_LAT, WAREHOUSE_LON, CHILDREN_PER_BOX)
    locations = [_location(lat=43.46, lon=-80.49, num_children=29)]
    with pytest.raises(ValueError, match="Cannot pack location"):
        await algo.cluster_locations_by_constraints(locations=locations)


@pytest.mark.asyncio
async def test_cluster_locations_raises_when_no_feasible_driver() -> None:
    """Greedy assignment fails when every route is full (empty feasible_indices)."""
    algo = SweepClusteringAlgorithm(WAREHOUSE_LAT, WAREHOUSE_LON, CHILDREN_PER_BOX)
    # 11 far stops, 2 drivers -> max 5 stops per far route -> capacity 10 total.
    far = [
        _location(
            lat=43.60,
            lon=-80.70,
            num_children=2,
            address="10 Main St, Elmira, ON",
        )
        for _ in range(11)
    ]
    with pytest.raises(ValueError, match="Cannot assign"):
        await algo.cluster_locations(
            locations=far,
            num_clusters=2,
            max_boxes_per_cluster=14,
        )

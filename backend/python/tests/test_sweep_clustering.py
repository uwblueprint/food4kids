"""Tests for SweepClusteringAlgorithm and the SweepRoutingAlgorithm engine."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any
from uuid import uuid4

import pytest

from app.models.location import Location
from app.schemas.route_generation import RouteGenerationSettings
from app.services.implementations import sweep_clustering
from app.services.implementations.sweep_clustering import (
    FAR_DISTANCE_KM_THRESHOLD,
    FAR_MAX_STOPS_PER_CLUSTER,
    SweepClusteringAlgorithm,
    SweepRoutingAlgorithm,
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
        delivery_type="School",
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
# Minutes spent at each stop (SystemSettings.dropoff_minutes) — the algorithm
# has no default of its own, so every test states one.
SERVICE_MINUTES_PER_STOP = 15
# Per-car box capacity these tests plan against. The algorithm takes it as a
# required argument; there is no cap to fall back on.
MAX_BOXES = 14


def _algo() -> SweepClusteringAlgorithm:
    return SweepClusteringAlgorithm(
        WAREHOUSE_LAT, WAREHOUSE_LON, CHILDREN_PER_BOX, SERVICE_MINUTES_PER_STOP
    )


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
    algo = _algo()
    locations = [
        _location(lat=43.46 + i * 0.01, lon=-80.49, num_children=2) for i in range(12)
    ]
    num_drivers = 4
    clusters = await algo.cluster_locations(
        locations=locations,
        num_clusters=num_drivers,
        max_boxes_per_cluster=MAX_BOXES,
    )
    assert len(clusters) == num_drivers
    assert sum(len(c) for c in clusters) == len(locations)


@pytest.mark.asyncio
async def test_capacity_must_be_passed_in() -> None:
    """There is no fallback cap: omitting the capacity is a TypeError, not a
    silent plan against some number nobody configured."""
    algo = _algo()
    locations = [_location(lat=43.46, lon=-80.49, num_children=4)]
    with pytest.raises(TypeError, match="max_boxes_per_cluster"):
        await algo.cluster_locations(locations=locations, num_clusters=1)  # type: ignore[call-arg]


@pytest.mark.asyncio
@pytest.mark.parametrize("max_boxes", [4, 10, 14])
async def test_oversized_location_is_rejected_against_the_given_cap(
    max_boxes: int,
) -> None:
    """The cap in the error is the one passed in, not a module constant."""
    algo = _algo()
    # ceil(num_children / 2) boxes, one box over the cap under test.
    locations = [
        _location(
            lat=43.46, lon=-80.49, num_children=(max_boxes + 1) * CHILDREN_PER_BOX
        )
    ]
    with pytest.raises(
        ValueError, match=f"exceeds the per-driver maximum of {max_boxes}"
    ):
        await algo.cluster_locations(
            locations=locations, num_clusters=1, max_boxes_per_cluster=max_boxes
        )


@pytest.mark.asyncio
async def test_each_cluster_respects_box_cap() -> None:
    algo = _algo()
    locations = [
        _location(lat=43.46 + i * 0.008, lon=-80.49 - i * 0.005, num_children=4)
        for i in range(10)
    ]
    clusters = await algo.cluster_locations(
        locations=locations,
        num_clusters=3,
        max_boxes_per_cluster=MAX_BOXES,
    )
    for cluster in clusters:
        assert sum(effective_boxes(loc, CHILDREN_PER_BOX) for loc in cluster) <= 14


@pytest.mark.asyncio
async def test_far_address_limits_stops_per_route() -> None:
    algo = _algo()
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
        max_boxes_per_cluster=MAX_BOXES,
    )
    for cluster in clusters:
        has_far = any("elmira" in loc.address.lower() for loc in cluster)
        if has_far:
            assert len(cluster) <= FAR_MAX_STOPS_PER_CLUSTER


@pytest.mark.asyncio
async def test_load_spread_across_drivers() -> None:
    algo = _algo()
    locations = [
        _location(lat=43.45 + i * 0.01, lon=-80.50, num_children=2) for i in range(8)
    ]
    clusters = await algo.cluster_locations(
        locations=locations,
        num_clusters=4,
        max_boxes_per_cluster=MAX_BOXES,
    )
    sizes = [len(c) for c in clusters]
    assert max(sizes) - min(sizes) <= 1


@pytest.mark.asyncio
async def test_far_route_caps_at_five_stops_when_max_stops_omitted() -> None:
    """Far routes are capped at FAR_MAX_STOPS_PER_CLUSTER stops."""
    algo = _algo()
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
        max_boxes_per_cluster=MAX_BOXES,
    )
    for cluster in clusters:
        assert len(cluster) <= FAR_MAX_STOPS_PER_CLUSTER


@pytest.mark.asyncio
async def test_far_by_haversine_distance_limits_stops() -> None:
    """Locations beyond FAR_DISTANCE_KM_THRESHOLD are far without a city keyword."""
    algo = _algo()
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
        max_boxes_per_cluster=MAX_BOXES,
    )
    for cluster in clusters:
        assert len(cluster) <= FAR_MAX_STOPS_PER_CLUSTER


@pytest.mark.asyncio
async def test_cluster_locations_by_constraints_flushes_on_box_cap() -> None:
    algo = _algo()
    # 4 boxes each (8 children); cap 14 -> at most 3 stops per cluster -> multiple clusters.
    locations = [
        _location(lat=43.46 + i * 0.005, lon=-80.49, num_children=8) for i in range(7)
    ]
    clusters = await algo.cluster_locations_by_constraints(
        locations=locations,
        max_boxes_per_cluster=MAX_BOXES,
    )
    assert len(clusters) >= 2
    assert sum(len(c) for c in clusters) == len(locations)
    for cluster in clusters:
        assert sum(effective_boxes(loc, CHILDREN_PER_BOX) for loc in cluster) <= 14


@pytest.mark.asyncio
async def test_cluster_locations_by_constraints_rejects_oversized_location() -> None:
    algo = _algo()
    locations = [_location(lat=43.46, lon=-80.49, num_children=29)]
    with pytest.raises(ValueError, match="Cannot pack location"):
        await algo.cluster_locations_by_constraints(
            locations=locations, max_boxes_per_cluster=MAX_BOXES
        )


@pytest.mark.asyncio
async def test_cluster_locations_raises_when_no_feasible_driver() -> None:
    """Greedy assignment fails when every route is full (empty feasible_indices)."""
    algo = _algo()
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
            max_boxes_per_cluster=MAX_BOXES,
        )


def _routing_settings(
    *, num_routes: int, max_boxes: int = MAX_BOXES, children_per_box: int = 2
) -> RouteGenerationSettings:
    return RouteGenerationSettings(
        route_start_time=datetime(2026, 7, 7, 9, 0),
        num_routes=num_routes,
        max_boxes_per_driver=max_boxes,
        children_per_box=children_per_box,
        service_time_minutes=SERVICE_MINUTES_PER_STOP,
    )


def _ring(count: int, num_children: int = 2) -> list[Location]:
    """Stops spread around the warehouse so the sweep has angles to order."""
    return [
        _location(
            lat=WAREHOUSE_LAT + 0.05 * math.sin(math.tau * i / count),
            lon=WAREHOUSE_LON + 0.05 * math.cos(math.tau * i / count),
            num_children=num_children,
            name=f"Stop {i}",
        )
        for i in range(count)
    ]


@pytest.mark.asyncio
async def test_routing_builds_clustering_from_call_time_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every configured number reaches clustering; none is baked in up front."""
    seen: dict[str, Any] = {}

    class SpyClustering(SweepClusteringAlgorithm):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            seen["init"] = kwargs
            super().__init__(*args, **kwargs)

        async def cluster_locations(
            self,
            locations: list[Location],
            num_clusters: int,
            max_boxes_per_cluster: int,
            timeout_seconds: float | None = None,
        ) -> list[list[Location]]:
            seen["cluster"] = {
                "locations": locations,
                "num_clusters": num_clusters,
                "max_boxes_per_cluster": max_boxes_per_cluster,
                "timeout_seconds": timeout_seconds,
            }
            return await super().cluster_locations(
                locations, num_clusters, max_boxes_per_cluster, timeout_seconds
            )

    monkeypatch.setattr(sweep_clustering, "SweepClusteringAlgorithm", SpyClustering)
    stops = _ring(6)

    await SweepRoutingAlgorithm().generate_routes(
        stops,
        WAREHOUSE_LAT,
        WAREHOUSE_LON,
        _routing_settings(num_routes=2, max_boxes=9, children_per_box=3),
        timeout_seconds=12.0,
    )

    assert seen["init"] == {
        "warehouse_lat": WAREHOUSE_LAT,
        "warehouse_lon": WAREHOUSE_LON,
        "children_per_box": 3,
        "service_minutes_per_stop": SERVICE_MINUTES_PER_STOP,
    }
    assert seen["cluster"] == {
        "locations": stops,
        "num_clusters": 2,
        "max_boxes_per_cluster": 9,
        "timeout_seconds": 12.0,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("num_routes", [1, 2, 3, 6])
async def test_routing_returns_every_stop_once_across_num_routes(
    num_routes: int,
) -> None:
    stops = _ring(6)

    routes = await SweepRoutingAlgorithm().generate_routes(
        stops,
        WAREHOUSE_LAT,
        WAREHOUSE_LON,
        _routing_settings(num_routes=num_routes),
    )

    assert len(routes) == num_routes
    returned = [stop.location_id for route in routes for stop in route]
    assert sorted(returned) == sorted(stop.location_id for stop in stops)


@pytest.mark.asyncio
async def test_routing_visits_each_route_in_sweep_order() -> None:
    """The cluster order is the visit order, so it must already be swept."""

    def angle(stop: Location) -> float:
        assert stop.latitude is not None and stop.longitude is not None
        return (
            math.atan2(stop.latitude - WAREHOUSE_LAT, stop.longitude - WAREHOUSE_LON)
            % math.tau
        )

    routes = await SweepRoutingAlgorithm().generate_routes(
        list(reversed(_ring(12))),
        WAREHOUSE_LAT,
        WAREHOUSE_LON,
        _routing_settings(num_routes=3),
    )

    for route in routes:
        angles = [angle(stop) for stop in route]
        assert angles == sorted(angles)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("children_per_box", "fits"),
    [
        (2, True),  # 4 children -> 2 boxes, at the cap of 2
        (1, False),  # 4 children -> 4 boxes, over the cap of 2
    ],
)
async def test_routing_enforces_the_configured_box_cap(
    children_per_box: int, fits: bool
) -> None:
    stops = _ring(1, num_children=4)
    settings = _routing_settings(
        num_routes=1, max_boxes=2, children_per_box=children_per_box
    )
    engine = SweepRoutingAlgorithm()

    if fits:
        routes = await engine.generate_routes(
            stops, WAREHOUSE_LAT, WAREHOUSE_LON, settings
        )
        assert routes == [stops]
    else:
        with pytest.raises(ValueError, match="per-driver maximum of 2"):
            await engine.generate_routes(stops, WAREHOUSE_LAT, WAREHOUSE_LON, settings)

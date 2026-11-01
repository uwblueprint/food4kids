"""Tests for SweepClusteringAlgorithm and the SweepRoutingAlgorithm engine."""

from __future__ import annotations

import math
import random
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


# --- Packing at (or near) the capacity minimum -------------------------------

ELMIRA = "10 Main St, Elmira, ON"


def _sized_ring(sizes: list[int], seed: int = 0) -> list[Location]:
    """Near stops at shuffled angles and radii, one per box size in ``sizes``."""
    rng = random.Random(seed)
    stops = []
    for i, boxes in enumerate(sizes):
        angle = rng.uniform(0, math.tau)
        radius = rng.uniform(0.02, 0.1)
        stops.append(
            _location(
                lat=WAREHOUSE_LAT + radius * math.sin(angle),
                lon=WAREHOUSE_LON + radius * math.cos(angle),
                # The most children that still round to ``boxes`` boxes.
                num_children=boxes * CHILDREN_PER_BOX,
                name=f"Stop {i}",
            )
        )
    return stops


def _one_and_two_box_sizes(total: int, seed: int) -> list[int]:
    """Random 1- and 2-box stops summing to exactly ``total`` boxes."""
    rng = random.Random(seed)
    sizes: list[int] = []
    while sum(sizes) < total:
        sizes.append(min(rng.choice((1, 2)), total - sum(sizes)))
    return sizes


def _assert_valid_routes(
    routes: list[list[Location]],
    stops: list[Location],
    num_routes: int,
    max_boxes: int,
    algo: SweepClusteringAlgorithm,
) -> None:
    assert len(routes) == num_routes
    assert sorted(s.location_id for r in routes for s in r) == sorted(
        s.location_id for s in stops
    )
    sweep_rank = {
        s.location_id: rank
        for rank, s in enumerate(algo._sorted_locations(stops, lambda: None))
    }
    for route in routes:
        assert sum(effective_boxes(s, CHILDREN_PER_BOX) for s in route) <= max_boxes
        ranks = [sweep_rank[s.location_id] for s in route]
        assert ranks == sorted(ranks), "route lost its sweep (visit) order"
        metrics = [algo._location_metrics(s) for s in route]
        if any(m.is_far for m in metrics):
            assert len(route) <= FAR_MAX_STOPS_PER_CLUSTER
            assert sum(m.stop_minutes for m in metrics) <= (
                algo._far_route_minutes_cap()
            )


async def test_exact_fit_with_mixed_box_sizes_regression() -> None:
    """The failing case from the offline experiment, in miniature: boxes fill
    every car exactly. Balancing by stop count used to strand the last 2-box
    stop with every car one box short."""
    algo = _algo()
    num_routes, max_boxes = 23, 10
    stops = _sized_ring(_one_and_two_box_sizes(num_routes * max_boxes, seed=1))

    routes = await algo.cluster_locations(stops, num_routes, max_boxes)

    _assert_valid_routes(routes, stops, num_routes, max_boxes, algo)
    assert all(
        sum(effective_boxes(s, CHILDREN_PER_BOX) for s in r) == max_boxes
        for r in routes
    )


@pytest.mark.parametrize(
    ("max_boxes", "num_routes", "slack"),
    [
        (max_boxes, num_routes, slack)
        for max_boxes in (2, 3, 4, 9, 10, 14)
        for num_routes in (1, 2, 5, 12)
        for slack in (0, 1, 3)
        # Every route needs at least one stop.
        if num_routes * max_boxes - slack >= num_routes
    ],
)
@pytest.mark.parametrize("seed", range(4))
async def test_one_and_two_box_stops_always_pack_when_boxes_fit(
    max_boxes: int, num_routes: int, slack: int, seed: int
) -> None:
    """With 1- and 2-box stops and no far routes, a packing exists exactly
    when the boxes fit and (for an odd cap) each car's 2-box stops fit in
    its even part. Every such instance must pack."""
    total = num_routes * max_boxes - slack
    sizes = _one_and_two_box_sizes(total, seed)
    if sizes.count(2) > num_routes * (max_boxes // 2):
        # Swap 2-box stops for pairs of 1-box stops until a packing exists.
        excess = sizes.count(2) - num_routes * (max_boxes // 2)
        sizes = [1] * (2 * excess) + sorted(sizes)[: len(sizes) - excess]
    while len(sizes) < num_routes:
        sizes.remove(2)
        sizes += [1, 1]
    assert sum(sizes) == total
    stops = _sized_ring(sizes, seed)
    algo = _algo()

    routes = await algo.cluster_locations(stops, num_routes, max_boxes)

    _assert_valid_routes(routes, stops, num_routes, max_boxes, algo)


async def test_two_box_stops_that_cannot_share_an_odd_cap_are_rejected() -> None:
    """9-box cars hold at most four 2-box stops each, so nine 2-box stops
    can't fill two cars even though 18 boxes is exactly their capacity."""
    stops = _sized_ring([2] * 9)
    with pytest.raises(ValueError, match="Cannot assign"):
        await _algo().cluster_locations(stops, 2, 9)


async def test_one_box_over_capacity_says_how_many_drivers_are_needed() -> None:
    stops = _sized_ring(_one_and_two_box_sizes(4 * 10 + 1, seed=0))
    with pytest.raises(
        ValueError,
        match=r"41 boxes need at least 5 drivers at 10 boxes each, but only 4",
    ):
        await _algo().cluster_locations(stops, 4, 10)


async def test_oversized_stop_is_rejected_even_when_the_total_fits() -> None:
    """An 11-box stop can't ride in any 10-box car, however empty the rest."""
    stops = _sized_ring([11, 1, 1])
    with pytest.raises(ValueError, match="exceeds the per-driver maximum of 10"):
        await _algo().cluster_locations(stops, 3, 10)


@pytest.mark.parametrize(
    ("sizes", "num_routes", "max_boxes", "packs"),
    [
        ([10, 10, 10], 3, 10, True),  # a full car per stop
        ([6, 4, 6, 4], 2, 10, True),  # needs 6+4 pairs
        ([7, 3, 5, 5, 2, 8], 3, 10, True),
        ([5, 3, 2, 4, 3, 3, 2, 3, 5], 3, 10, True),  # exact fit, mixed
        ([6, 6, 6], 2, 10, False),  # 18 of 20 boxes, but no two share a car
        ([7, 7, 3, 3], 2, 10, True),
        ([4, 4, 4, 4, 4], 2, 10, False),  # 20 of 20, but 4+4+4 > 10
    ],
)
async def test_mixed_larger_box_sizes(
    sizes: list[int], num_routes: int, max_boxes: int, packs: bool
) -> None:
    """Larger stops: the repair finds these packings, and a total that fits
    is not mistaken for a packing that exists."""
    stops = _sized_ring(sizes)
    algo = _algo()
    if packs:
        routes = await algo.cluster_locations(stops, num_routes, max_boxes)
        _assert_valid_routes(routes, stops, num_routes, max_boxes, algo)
    else:
        with pytest.raises(ValueError, match="Cannot assign"):
            await algo.cluster_locations(stops, num_routes, max_boxes)


def _far_stop(boxes: int, name: str = "Far") -> Location:
    return _location(
        lat=43.60,
        lon=-80.70,
        num_children=boxes * CHILDREN_PER_BOX,
        address=ELMIRA,
        name=name,
    )


async def test_far_route_trades_small_stops_for_big_ones_to_fit_everything() -> None:
    """A far route holds at most five stops, so at an exact fit it needs a
    2-box far stop and four 2-box near stops. The sweep hands it whatever
    comes round; the repair has to swap its 1-box stops out."""
    algo = _algo()
    num_routes, max_boxes = 4, 10
    far = _far_stop(2)
    near_sizes = _one_and_two_box_sizes(num_routes * max_boxes - 2, seed=3)
    assert near_sizes.count(2) >= 4
    stops = [far, *_sized_ring(near_sizes, seed=3)]

    routes = await algo.cluster_locations(stops, num_routes, max_boxes)

    _assert_valid_routes(routes, stops, num_routes, max_boxes, algo)
    (far_route,) = [r for r in routes if far in r]
    assert [effective_boxes(s, CHILDREN_PER_BOX) for s in far_route] == [2] * 5


async def test_far_route_with_a_one_box_far_stop_cannot_fill_its_car() -> None:
    """Five stops at most, one of them a single box: a far route tops out at
    9 boxes, so an exact fit with a 1-box far stop has no packing. The same
    boxes all near the warehouse do pack."""
    algo = _algo()
    near = _sized_ring([2] * 14 + [1], seed=0)
    assert sum(effective_boxes(s, CHILDREN_PER_BOX) for s in near) == 29

    with pytest.raises(ValueError, match="far-route caps"):
        await algo.cluster_locations([_far_stop(1), *near], 3, 10)
    near_only = [*near, *_sized_ring([1], seed=1)]
    routes = await algo.cluster_locations(near_only, 3, 10)
    _assert_valid_routes(routes, near_only, 3, 10, algo)


async def test_far_stops_on_separate_routes_each_get_their_own_cap() -> None:
    """Two far stops at an exact fit: each needs its own route of big stops."""
    algo = _algo()
    num_routes, max_boxes = 5, 10
    far = [_far_stop(2, "Far A"), _far_stop(2, "Far B")]
    near = _sized_ring(
        _one_and_two_box_sizes(num_routes * max_boxes - 4, seed=7), seed=7
    )
    stops = far + near

    routes = await algo.cluster_locations(stops, num_routes, max_boxes)

    _assert_valid_routes(routes, stops, num_routes, max_boxes, algo)


async def test_far_routes_pack_with_slack_across_many_seeds() -> None:
    """Near-fit instances with a few far stops all pack and keep far caps."""
    algo = _algo()
    for seed in range(25):
        rng = random.Random(seed)
        num_routes, max_boxes = rng.randint(3, 8), 10
        far = [_far_stop(2, f"Far {i}") for i in range(rng.randint(1, 2))]
        near_total = num_routes * max_boxes - 2 * len(far) - rng.randint(1, 3)
        stops = far + _sized_ring(_one_and_two_box_sizes(near_total, seed), seed)

        routes = await algo.cluster_locations(stops, num_routes, max_boxes)

        _assert_valid_routes(routes, stops, num_routes, max_boxes, algo)


def test_failed_placement_leaves_routes_untouched() -> None:
    """A repair that can't finish must roll back every move it tried."""
    algo = _algo()
    stops = _sized_ring([4, 4, 4, 4, 4])
    metrics = algo._metrics_for_locations(stops)
    clusters = [sweep_clustering._ClusterState() for _ in range(2)]
    journal: list[tuple[int, sweep_clustering._ClusterState]] = []
    for stop, index in zip(stops[:4], [0, 0, 1, 1], strict=True):
        algo._add_to_cluster(clusters[index], stop, metrics[stop.location_id])
    before = [list(c.locations) for c in clusters]

    placed = algo._place(
        location=stops[4],
        clusters=clusters,
        journal=journal,
        max_boxes=10,
        metrics_by_id=metrics,
        depth=sweep_clustering.REPAIR_DEPTH,
        locked=frozenset(),
        check_timeout=lambda: None,
    )

    assert not placed
    assert [list(c.locations) for c in clusters] == before
    assert [c.box_count for c in clusters] == [8, 8]
    assert journal == []


def test_repair_checks_the_timeout() -> None:
    """The repair search polls the deadline, so a slow one can't overrun it."""
    algo = _algo()
    stops = _sized_ring([1, 1, 2])
    metrics = algo._metrics_for_locations(stops)
    clusters = [sweep_clustering._ClusterState() for _ in range(2)]
    for stop, cluster in zip(stops[:2], clusters, strict=True):
        algo._add_to_cluster(cluster, stop, metrics[stop.location_id])

    def expired() -> None:
        raise sweep_clustering.TimeoutError("deadline")

    # Each 2-box car has one box free: placing the 2-box stop needs a repair.
    with pytest.raises(sweep_clustering.TimeoutError):
        algo._place(
            location=stops[2],
            clusters=clusters,
            journal=[],
            max_boxes=2,
            metrics_by_id=metrics,
            depth=sweep_clustering.REPAIR_DEPTH,
            locked=frozenset(),
            check_timeout=expired,
        )


async def test_far_stop_last_in_the_sweep_still_gets_a_short_route() -> None:
    """A far stop just short of a full turn is swept last, when every route
    already has more stops than a far route may. It must still be placed,
    and as a 1-box stop it has no smaller stops to swap in for."""
    algo = _algo()
    # ~40 km east, slightly south: an angle just under 2*pi.
    far = _location(
        lat=WAREHOUSE_LAT - 0.01,
        lon=WAREHOUSE_LON + 0.5,
        num_children=CHILDREN_PER_BOX,
        name="Far east",
    )
    near = _sized_ring([1] * 24, seed=4)
    stops = [far, *near]
    assert algo._sorted_locations(stops, lambda: None)[-1] is far
    assert algo._location_metrics(far).is_far

    routes = await algo.cluster_locations(stops, 4, 10)

    _assert_valid_routes(routes, stops, 4, 10, algo)

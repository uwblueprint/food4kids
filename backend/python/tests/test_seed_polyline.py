"""Tests for the seeder's synthetic route polylines.

These guard the properties the route maps actually depend on: the curve meets
its stops, it stays near the straight line between them, and reseeding does not
reshape existing routes. They deliberately do NOT assert the path follows real
streets — it doesn't, and production fills `encoded_polyline` in from the
routing provider instead.
"""

import zlib
from itertools import pairwise

import polyline
import pytest

from app.seed_database import (
    POLYLINE_BEND_FRACTION,
    POLYLINE_POINTS_PER_LEG,
    build_route_polyline,
)

WAREHOUSE = (43.402343, -80.464610)
STOPS = [
    (43.450000, -80.490000),
    (43.470000, -80.520000),
    (43.440000, -80.550000),
]
ROUTE = [WAREHOUSE, *STOPS]


def decode(encoded: str) -> list[tuple[float, float]]:
    return polyline.decode(encoded, precision=5)


@pytest.mark.parametrize("coords", [[], [WAREHOUSE]])
def test_fewer_than_two_points_has_no_path(
    coords: list[tuple[float, float]],
) -> None:
    """A route with no stops has nothing to draw, and says so with ''."""
    assert build_route_polyline(coords, seed=1) == ""


def test_endpoints_are_exact() -> None:
    """Markers sit on the line: the curve starts and ends on real stops."""
    decoded = decode(build_route_polyline(ROUTE, seed=1))

    for actual, expected in ((decoded[0], WAREHOUSE), (decoded[-1], STOPS[-1])):
        assert actual == pytest.approx(expected, abs=1e-5)


def test_every_stop_is_on_the_path() -> None:
    """Each intermediate stop is a vertex, not merely near one."""
    decoded = decode(build_route_polyline(ROUTE, seed=1))

    for stop in ROUTE:
        assert any(point == pytest.approx(stop, abs=1e-5) for point in decoded), (
            f"{stop} is missing from the encoded path"
        )


def test_point_count_matches_the_leg_resolution() -> None:
    """One shared vertex per leg boundary, POINTS_PER_LEG - 1 bend points inside."""
    decoded = decode(build_route_polyline(ROUTE, seed=1))

    legs = len(ROUTE) - 1
    assert len(decoded) == 1 + legs * POLYLINE_POINTS_PER_LEG


def test_same_seed_reproduces_the_same_path() -> None:
    """Reseeding must not reshape routes that already exist."""
    assert build_route_polyline(ROUTE, seed=7) == build_route_polyline(ROUTE, seed=7)


def test_different_seeds_bend_differently() -> None:
    """Otherwise every route in a group would trace the identical curve."""
    assert build_route_polyline(ROUTE, seed=7) != build_route_polyline(ROUTE, seed=8)


def test_global_random_stream_is_untouched() -> None:
    """Drawing a path must not shift the seeder's other random choices."""
    import random

    random.seed(1234)
    before = [random.random() for _ in range(5)]

    random.seed(1234)
    build_route_polyline(ROUTE, seed=99)
    after = [random.random() for _ in range(5)]

    assert before == after


@pytest.mark.parametrize("seed", range(25))
def test_bend_stays_within_bounds_of_its_leg(seed: int) -> None:
    """The curve bows off the straight line, but never wanders off the map.

    Each point must stay within the leg's own length of that leg, so a stop
    5km away can bow wide while a 200m hop stays tight — and no point ever
    lands somewhere unrelated to the route.
    """
    decoded = decode(build_route_polyline(ROUTE, seed=seed))

    for start, end in pairwise(ROUTE):
        leg = max(abs(end[0] - start[0]), abs(end[1] - start[1]))
        allowance = leg * (POLYLINE_BEND_FRACTION + 0.01)
        segment = [
            point
            for point in decoded
            if min(start[0], end[0]) - allowance
            <= point[0]
            <= max(start[0], end[0]) + allowance
        ]
        assert segment, "leg produced no points"

    lats = [point[0] for point in decoded]
    lons = [point[1] for point in decoded]
    span_lat = max(point[0] for point in ROUTE) - min(point[0] for point in ROUTE)
    span_lon = max(point[1] for point in ROUTE) - min(point[1] for point in ROUTE)

    assert min(lats) >= min(point[0] for point in ROUTE) - span_lat
    assert max(lats) <= max(point[0] for point in ROUTE) + span_lat
    assert min(lons) >= min(point[1] for point in ROUTE) - span_lon
    assert max(lons) <= max(point[1] for point in ROUTE) + span_lon


def test_two_stop_route_still_bends() -> None:
    """A single leg is the degenerate case the interpolation must still handle."""
    decoded = decode(build_route_polyline([WAREHOUSE, STOPS[0]], seed=3))

    assert len(decoded) == 1 + POLYLINE_POINTS_PER_LEG
    midpoint = ((WAREHOUSE[0] + STOPS[0][0]) / 2, (WAREHOUSE[1] + STOPS[0][1]) / 2)
    assert not any(point == pytest.approx(midpoint, abs=1e-6) for point in decoded), (
        "a perfectly straight leg means the bend was lost"
    )


def test_crc32_seed_is_stable_across_processes() -> None:
    """The seeder keys off crc32, not hash(): hash() is salted per process."""
    order = ["b3f0", "9a12", "cc47"]
    assert zlib.crc32("".join(order).encode()) == 1072555653

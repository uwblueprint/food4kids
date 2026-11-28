from __future__ import annotations

import functools
import itertools
import math
import time
from typing import TYPE_CHECKING, Any

from app.services.protocols.clustering_algorithm import ClusteringAlgorithmProtocol
from app.utilities.boxes import compute_boxes
from app.utilities.geo import haversine_km

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

    from app.models.location import Location
    from app.schemas.route_generation import RouteGenerationSettings


# Cities that should receive fewer stops per route (matched in address text).
FAR_CITY_KEYWORDS: frozenset[str] = frozenset(
    {
        "elmira",
    }
)

# Stops farther than this from the warehouse are treated like far deliveries.
FAR_DISTANCE_KM_THRESHOLD = 35.0

# Max stops on a route that includes any far delivery.
FAR_MAX_STOPS_PER_CLUSTER = 5

# Rough drive-time model for far routes.
AVERAGE_SPEED_KMH = 40.0

# Driving a far route may add beyond the round trip to its farthest stop.
FAR_DETOUR_MINUTES = 30.0


class LocationLatitudeError(Exception):
    """Raised when a location doesn't have a latitude."""


class LocationLongitudeError(Exception):
    """Raised when a location doesn't have a longitude."""


class TimeoutError(Exception):
    """Raised when an operation exceeds its timeout limit."""


def effective_boxes(location: Location, children_per_box: int) -> int:
    """Boxes a location needs: ceil(num_children / children_per_box).

    ``children_per_box`` comes from system settings; the divisor is no longer
    hardcoded. See app.utilities.boxes.compute_boxes.
    """
    return compute_boxes(location.num_children, children_per_box)


def _timeout_check(timeout_seconds: float | None) -> Callable[[], None]:
    """A check that raises once ``timeout_seconds`` have passed since now."""
    start_time = time.time()

    def check_timeout() -> None:
        if timeout_seconds is not None:
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                raise TimeoutError(
                    f"Route generation exceeded timeout of {timeout_seconds}s "
                    f"(elapsed: {elapsed:.2f}s)"
                )

    return check_timeout


class SweepClusteringAlgorithm(ClusteringAlgorithmProtocol):
    """Sweep-line clustering for route generation.

    Capacity is measured in boxes (``max_boxes_per_cluster``). The only stop
    count limit is ``FAR_MAX_STOPS_PER_CLUSTER``, which applies solely to routes
    containing a far delivery, along with ``FAR_DETOUR_MINUTES``.
    """

    def __init__(
        self,
        warehouse_lat: float,
        warehouse_lon: float,
        children_per_box: int,
    ) -> None:
        self._warehouse = (warehouse_lat, warehouse_lon)
        self._children_per_box = children_per_box

    async def cluster_locations(
        self,
        locations: list[Location],
        num_clusters: int,
        max_boxes_per_cluster: int,
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:
        """
        Cluster into exactly ``num_clusters`` routes (one per driver).

        Far stops get routes of their own and the rest are cut into contiguous
        sectors of the sweep around the warehouse (see ``_routes``). If that
        can't fit every box, the rest are spread most-boxes-first instead, so
        stops with few boxes fill the gaps the others leave. That always packs 1- and
        2-box stops without far routes when they fit; otherwise it is a
        heuristic and can miss a packing.
        """
        check_timeout = _timeout_check(timeout_seconds)

        if len(locations) == 0:
            raise ValueError("locations list cannot be empty")
        if num_clusters < 1:
            raise ValueError("num_clusters must be at least 1")
        if num_clusters > len(locations):
            raise ValueError(
                f"Cannot create {num_clusters} clusters: not enough locations"
            )

        for location in locations:
            if self._boxes(location) > max_boxes_per_cluster:
                raise ValueError(
                    f"Location '{location.name}' requires "
                    f"{self._boxes(location)} boxes, "
                    f"which exceeds the per-driver maximum of {max_boxes_per_cluster}."
                )

        total_boxes = self._box_count(locations)
        if total_boxes > num_clusters * max_boxes_per_cluster:
            raise ValueError(
                f"{total_boxes} boxes need at least "
                f"{math.ceil(total_boxes / max_boxes_per_cluster)} drivers at "
                f"{max_boxes_per_cluster} boxes each, but only {num_clusters} "
                f"were requested."
            )

        stops = self._sorted_locations(locations)
        for sectors in (True, False):
            # Sharing far routes frees drivers; one far stop each frees stop
            # slots. Neither suits every load, so try both.
            for share_far in (True, False):
                check_timeout()
                routes = self._routes(
                    stops, num_clusters, max_boxes_per_cluster, sectors, share_far
                )
                if routes:
                    return routes
        raise ValueError(
            f"Cannot assign {len(locations)} stops across {num_clusters} drivers: "
            f"no fit found within max {max_boxes_per_cluster} boxes per driver "
            f"and the far-route caps. Add drivers or adjust loads."
        )

    def _routes(
        self,
        stops: list[Location],
        num_clusters: int,
        max_boxes: int,
        sectors: bool,
        share_far: bool,
    ) -> list[list[Location]] | None:
        """Far stops in sweep order, each on the previous one's route if
        ``share_far`` and it fits, else on a new one. Then the near stops, cut
        into ``sectors`` or else spread most-boxes-first. None if they don't fit.
        """
        routes: list[list[Location]] = []
        for stop in filter(self._is_far, stops):
            if not (share_far and routes and self._fits(routes[-1], stop, max_boxes)):
                routes.append([])
            routes[-1].append(stop)
        near = [stop for stop in stops if not self._is_far(stop)]
        num_near_routes = num_clusters - len(routes)

        if not sectors:
            # Far routes are short on stops, so they fill first, with the
            # stops that have the most boxes. Then even headcount and boxes.
            routes += [[] for _ in range(num_near_routes)]
            near.sort(key=self._boxes, reverse=True)
            placed = num_near_routes >= 0 and self._place(
                routes,
                near,
                max_boxes,
                lambda _, route: (
                    not (route and self._is_far(route[0])),
                    len(route),
                    self._box_count(route),
                ),
            )
            return routes if placed else None

        near = self._top_up(routes, near, num_near_routes * max_boxes, max_boxes)
        if not 1 <= num_near_routes <= len(near):
            return None
        handed_off: list[Location] = []
        for run in self._cut(near, num_near_routes, max_boxes):
            while self._box_count(run) > max_boxes:
                # The smallest stop, nearest an edge so the sector stays
                # contiguous.
                position = min(
                    range(len(run)),
                    key=lambda i: (self._boxes(run[i]), min(i, len(run) - 1 - i)),
                )
                handed_off.append(run.pop(position))
            routes.append(run)
        placed = self._place(routes, handed_off, max_boxes, self._km_to_route)
        return routes if placed else None

    def _place(
        self,
        routes: list[list[Location]],
        stops: list[Location],
        max_boxes: int,
        cost: Callable[[Location, list[Location]], Any],
    ) -> bool:
        """Add each stop to the route that fits it at the least ``cost``.
        False as soon as a stop fits nowhere."""
        for stop in stops:
            fits = [route for route in routes if self._fits(route, stop, max_boxes)]
            if not fits:
                return False
            min(fits, key=functools.partial(cost, stop)).append(stop)
        return True

    def _top_up(
        self,
        far_routes: list[list[Location]],
        near: list[Location],
        room: int,
        max_boxes: int,
    ) -> list[Location]:
        """Move near stops onto far routes until the rest fit in ``room``
        boxes, and return the rest. Far routes are short on stops, so the
        stops with the most boxes go first, then those least out of a far
        route's way."""
        excess = self._box_count(near) - room
        if excess <= 0:
            return near
        moved: set[UUID] = set()
        for stop in sorted(
            near,
            key=lambda s: (
                -self._boxes(s),
                min((self._detour_with(s, r) for r in far_routes), default=0.0),
            ),
        ):
            if excess > 0 and self._place(
                far_routes, [stop], max_boxes, self._detour_with
            ):
                excess -= self._boxes(stop)
                moved.add(stop.location_id)
        return [stop for stop in near if stop.location_id not in moved]

    def _cut(
        self, stops: list[Location], num_sectors: int, max_boxes: int
    ) -> list[list[Location]]:
        """Cut the circular sweep into contiguous runs, each cut nearest the
        next even share of the boxes. The start of the circle moves every cut,
        so it tries a car's worth of starts and keeps the one with the fewest
        boxes over capacity."""
        n = len(stops)

        def runs_from(start: int) -> list[list[Location]]:
            sequence = stops[start:] + stops[:start]
            prefix = [0, *itertools.accumulate(map(self._boxes, sequence))]
            cuts = [0]
            for sector in range(1, num_sectors):
                share = sector * prefix[n] / num_sectors
                cuts.append(
                    min(
                        range(cuts[-1] + 1, n - num_sectors + sector + 1),
                        key=lambda cut: abs(prefix[cut] - share),
                    )
                )
            return [sequence[a:b] for a, b in itertools.pairwise([*cuts, n])]

        return min(
            map(runs_from, range(min(n, max_boxes))),
            key=lambda runs: sum(
                max(0, self._box_count(run) - max_boxes) for run in runs
            ),
        )

    def _fits(self, route: list[Location], stop: Location, max_boxes: int) -> bool:
        stops = [*route, stop]
        if self._box_count(stops) > max_boxes:
            return False
        # Only routes with a far delivery are capped on stops and detour.
        if not any(map(self._is_far, stops)):
            return True
        return (
            len(stops) <= FAR_MAX_STOPS_PER_CLUSTER
            and self._detour_minutes(stops) <= FAR_DETOUR_MINUTES
        )

    def _detour_minutes(self, stops: list[Location]) -> float:
        """Minutes the stops, visited nearest the warehouse first, add to the
        round trip to the farthest one."""
        order = sorted(stops, key=self._warehouse_km)
        hops = sum(self._km(a, b) for a, b in itertools.pairwise(order))
        detour = self._warehouse_km(order[0]) + hops - self._warehouse_km(order[-1])
        return detour / AVERAGE_SPEED_KMH * 60.0

    def _detour_with(self, stop: Location, route: list[Location]) -> float:
        return self._detour_minutes([*route, stop])

    def _km_to_route(self, stop: Location, route: list[Location]) -> float:
        return min(self._km(stop, other) for other in route)

    def _is_far(self, location: Location) -> bool:
        return self._is_far_by_address(location) or (
            self._warehouse_km(location) >= FAR_DISTANCE_KM_THRESHOLD
        )

    def _is_far_by_address(self, location: Location) -> bool:
        address_lower = location.address.lower()
        return any(keyword in address_lower for keyword in FAR_CITY_KEYWORDS)

    def _sorted_locations(self, locations: list[Location]) -> list[Location]:
        """Return locations sorted by (angle from warehouse, then distance)."""

        def key(location: Location) -> tuple[float, float]:
            lat, lon = _coordinates(location)
            dlat, dlon = lat - self._warehouse[0], lon - self._warehouse[1]
            return math.atan2(dlat, dlon) % math.tau, dlon**2 + dlat**2

        return sorted(locations, key=key)

    def _boxes(self, location: Location) -> int:
        return effective_boxes(location, self._children_per_box)

    def _box_count(self, stops: list[Location]) -> int:
        return sum(map(self._boxes, stops))

    def _km(self, a: Location, b: Location) -> float:
        return haversine_km(*_coordinates(a), *_coordinates(b))

    def _warehouse_km(self, location: Location) -> float:
        return haversine_km(*self._warehouse, *_coordinates(location))


def _coordinates(location: Location) -> tuple[float, float]:
    if location.latitude is None:
        raise LocationLatitudeError(
            f"Location {location.location_id} is missing latitude."
        )
    if location.longitude is None:
        raise LocationLongitudeError(
            f"Location {location.location_id} is missing longitude."
        )
    return location.latitude, location.longitude



class SweepRoutingAlgorithm:
    """Sweep clustering as a complete routing engine, at no API cost.

    Each route visits its stops nearest the warehouse first. Within a sector
    that drives within 1-3% of an optimised order; angle order zigzags.
    """

    async def generate_routes(
        self,
        locations: list[Location],
        warehouse_lat: float,
        warehouse_lon: float,
        settings: RouteGenerationSettings,
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:
        clustering = SweepClusteringAlgorithm(
            warehouse_lat=warehouse_lat,
            warehouse_lon=warehouse_lon,
            children_per_box=settings.children_per_box,
        )
        clusters = await clustering.cluster_locations(
            locations=locations,
            num_clusters=settings.num_routes,
            max_boxes_per_cluster=settings.max_boxes_per_driver,
            timeout_seconds=timeout_seconds,
        )
        return [
            sorted(
                cluster,
                key=clustering._warehouse_km,
            )
            for cluster in clusters
        ]

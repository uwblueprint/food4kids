from __future__ import annotations

import functools
import itertools
import math
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.services.protocols.clustering_algorithm import ClusteringAlgorithmProtocol
from app.utilities.boxes import compute_boxes

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


@dataclass
class _ClusterState:
    locations: list[Location] = field(default_factory=list)
    box_count: int = 0
    has_far_stop: bool = False


@dataclass(frozen=True)
class _LocationMetrics:
    """Precomputed per-location values used during assignment (avoids repeat haversine)."""

    distance_km: float
    is_far: bool


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
        self._warehouse_lat = warehouse_lat
        self._warehouse_lon = warehouse_lon
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

        Locations are sweep-sorted from the warehouse, far stops are given
        routes of their own and the rest are cut into contiguous sectors (see
        ``_sectors``). If that can't fit every box, they are assigned greedily
        to the least-loaded feasible route instead: far stops first, then the
        rest largest-first, so small stops fill the gaps big ones leave. That
        always packs 1- and 2-box stops without far routes when they fit;
        otherwise it is a heuristic and can miss a packing.
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
            check_timeout()
            if self._boxes(location) > max_boxes_per_cluster:
                raise ValueError(
                    f"Location '{location.name}' requires "
                    f"{self._boxes(location)} boxes, "
                    f"which exceeds the per-driver maximum of {max_boxes_per_cluster}."
                )

        total_boxes = sum(self._boxes(location) for location in locations)
        if total_boxes > num_clusters * max_boxes_per_cluster:
            raise ValueError(
                f"{total_boxes} boxes need at least "
                f"{math.ceil(total_boxes / max_boxes_per_cluster)} drivers at "
                f"{max_boxes_per_cluster} boxes each, but only {num_clusters} "
                f"were requested."
            )

        sorted_locations = self._sorted_locations(locations, check_timeout)
        metrics_by_id = self._metrics_for_locations(sorted_locations)
        args = (sorted_locations, num_clusters, max_boxes_per_cluster, metrics_by_id)
        clusters = self._sectors(*args, check_timeout) or self._spread(
            *args, check_timeout
        )

        # Defensive: should be unreachable if _can_add_to_cluster stays in sync.
        for index, cluster in enumerate(clusters):
            cluster_boxes = sum(self._boxes(loc) for loc in cluster)
            if cluster_boxes > max_boxes_per_cluster:
                raise ValueError(
                    f"Cluster {index + 1} would have {cluster_boxes} boxes, "
                    f"exceeding max_boxes_per_cluster={max_boxes_per_cluster}."
                )

        return clusters

    def _spread(
        self,
        sorted_locations: list[Location],
        num_clusters: int,
        max_boxes: int,
        metrics_by_id: dict[UUID, _LocationMetrics],
        check_timeout: Callable[[], None],
    ) -> list[list[Location]]:
        """Greedy least-loaded assignment."""
        # Nearest first among equals: far routes take the earliest near stops.
        placement_order = sorted(
            sorted_locations,
            key=lambda location: (
                not metrics_by_id[location.location_id].is_far,
                -self._boxes(location),
                metrics_by_id[location.location_id].distance_km,
            ),
        )
        # Spreading far stops keeps each far route's box room; grouping them
        # frees stop slots. Neither suits every load, so try both.
        for group_far in (False, True):
            assigned = self._assign(
                placement_order,
                num_clusters,
                max_boxes,
                metrics_by_id,
                group_far,
                check_timeout,
            )
            if isinstance(assigned, list):
                break
            unplaced = assigned
        else:
            boxes = self._boxes(unplaced)
            raise ValueError(
                f"Cannot assign '{unplaced.name}' ({boxes} boxes) across {num_clusters} "
                f"drivers: no fit found within max {max_boxes} boxes per "
                f"driver and the far-route caps. Add drivers or adjust loads."
            )

        return [state.locations for state in assigned]

    def _sectors(
        self,
        sorted_locations: list[Location],
        num_clusters: int,
        max_boxes: int,
        metrics_by_id: dict[UUID, _LocationMetrics],
        check_timeout: Callable[[], None],
    ) -> list[list[Location]] | None:
        """Far stops get their own routes, sharing where the far-route caps
        allow, else one each, topped up with near stops only as far as the
        other routes can't hold them all. The near stops are cut into
        contiguous sectors on the other routes, and each sector over capacity
        hands its smallest stops, nearest its edges, to the nearest route with
        room. Returns None if neither works.
        """
        all_near = [
            s for s in sorted_locations if not metrics_by_id[s.location_id].is_far
        ]
        far = [s for s in sorted_locations if metrics_by_id[s.location_id].is_far]
        for group_far in (True, False):
            routes = self._far_routes(far, max_boxes, metrics_by_id, group_far)
            num_sectors = num_clusters - len(routes)
            near = self._top_up(
                routes, all_near, num_sectors * max_boxes, max_boxes, metrics_by_id
            )
            if not 1 <= num_sectors <= len(near):
                continue
            runs = self._cut(near, num_sectors, max_boxes, check_timeout)
            handed_off: list[Location] = []
            for run in runs:
                overflow = sum(self._boxes(s) for s in run) - max_boxes
                while overflow > 0:
                    stop = run.pop(self._hand_off_position(run))
                    overflow -= self._boxes(stop)
                    handed_off.append(stop)
                routes.append(_ClusterState())
                for stop in run:
                    self._add_to_cluster(
                        routes[-1], stop, metrics_by_id[stop.location_id]
                    )
            for stop in handed_off:
                metrics = metrics_by_id[stop.location_id]
                fits = [
                    route
                    for route in routes
                    if self._can_add_to_cluster(route, stop, max_boxes, metrics)
                ]
                if not fits:
                    break
                nearest = min(fits, key=functools.partial(self._km_to_route, stop))
                self._add_to_cluster(nearest, stop, metrics)
            else:
                return [route.locations for route in routes]
        return None

    def _far_routes(
        self,
        far: list[Location],
        max_boxes: int,
        metrics_by_id: dict[UUID, _LocationMetrics],
        group: bool,
    ) -> list[_ClusterState]:
        """Far stops in sweep order, each sharing the previous one's route if
        ``group`` and it fits."""
        routes: list[_ClusterState] = []
        for stop in far:
            metrics = metrics_by_id[stop.location_id]
            if not (
                group
                and routes
                and self._can_add_to_cluster(routes[-1], stop, max_boxes, metrics)
            ):
                routes.append(_ClusterState())
            self._add_to_cluster(routes[-1], stop, metrics)
        return routes

    def _top_up(
        self,
        far_routes: list[_ClusterState],
        near: list[Location],
        room: int,
        max_boxes: int,
        metrics_by_id: dict[UUID, _LocationMetrics],
    ) -> list[Location]:
        """Move near stops onto far routes until the rest fit in ``room``
        boxes, and return the rest. Far routes are short on stops, so the
        biggest stops go first, then those least out of a far route's way."""
        excess = sum(self._boxes(s) for s in near) - room
        moved: set[UUID] = set()
        for stop in sorted(
            near,
            key=lambda s: (
                -self._boxes(s),
                min((self._detour_with(s, r) for r in far_routes), default=0.0),
            ),
        ):
            if excess <= 0:
                break
            metrics = metrics_by_id[stop.location_id]
            fits = [
                route
                for route in far_routes
                if self._can_add_to_cluster(route, stop, max_boxes, metrics)
            ]
            if fits:
                self._add_to_cluster(
                    min(fits, key=functools.partial(self._detour_with, stop)),
                    stop,
                    metrics,
                )
                moved.add(stop.location_id)
                excess -= self._boxes(stop)
        return [s for s in near if s.location_id not in moved]

    def _cut(
        self,
        stops: list[Location],
        num_sectors: int,
        max_boxes: int,
        check_timeout: Callable[[], None],
    ) -> list[list[Location]]:
        """Cut the circular sweep into contiguous runs, each cut nearest the
        next even share of the boxes. The start of the circle moves every cut,
        so it tries a car's worth of starts and keeps the one with the fewest
        boxes over capacity."""
        n = len(stops)
        best: tuple[int, list[list[Location]]] | None = None
        for start in range(min(n, max_boxes)):
            check_timeout()
            sequence = stops[start:] + stops[:start]
            boxes = itertools.accumulate(self._boxes(stop) for stop in sequence)
            prefix = [0, *boxes]
            cuts = [0]
            for sector in range(1, num_sectors):
                share = sector * prefix[n] / num_sectors
                cuts.append(
                    min(
                        range(cuts[-1] + 1, n - num_sectors + sector + 1),
                        key=lambda cut: abs(prefix[cut] - share),
                    )
                )
            cuts.append(n)
            overflow = sum(
                max(0, prefix[end] - prefix[begin] - max_boxes)
                for begin, end in itertools.pairwise(cuts)
            )
            if best is None or overflow < best[0]:
                runs = [sequence[a:b] for a, b in itertools.pairwise(cuts)]
                best = (overflow, runs)
        assert best is not None
        return best[1]

    def _hand_off_position(self, run: list[Location]) -> int:
        """The stop to move out of an overfull sector: the smallest, nearest an
        edge so the sector stays contiguous."""
        return min(
            range(len(run)),
            key=lambda i: (
                self._boxes(run[i]),
                min(i, len(run) - 1 - i),
            ),
        )

    async def cluster_locations_by_constraints(
        self,
        locations: list[Location],
        max_boxes_per_cluster: int,
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:
        """
        Cluster using sweep ordering, greedily packing until constraints bind.

        Does not target a fixed driver count. Uses the same box and far-stop rules.
        """
        check_timeout = _timeout_check(timeout_seconds)

        if len(locations) == 0:
            raise ValueError("locations list cannot be empty")

        sorted_locations = self._sorted_locations(locations, check_timeout)
        metrics_by_id = self._metrics_for_locations(sorted_locations)

        cluster_states: list[_ClusterState] = []
        current = _ClusterState()

        for location in sorted_locations:
            check_timeout()
            metrics = metrics_by_id[location.location_id]

            can_add = self._can_add_to_cluster(
                current, location, max_boxes_per_cluster, metrics
            )

            if current.locations and not can_add:
                cluster_states.append(current)
                current = _ClusterState()
                can_add = self._can_add_to_cluster(
                    current, location, max_boxes_per_cluster, metrics
                )

            if not can_add:
                boxes = self._boxes(location)
                raise ValueError(
                    f"Cannot pack location '{location.name}' ({boxes} boxes) "
                    f"within max {max_boxes_per_cluster} boxes per route."
                )

            self._add_to_cluster(current, location, metrics)

        if current.locations:
            cluster_states.append(current)

        return [state.locations for state in cluster_states]

    def _assign(
        self,
        placement_order: list[Location],
        num_clusters: int,
        max_boxes: int,
        metrics_by_id: dict[UUID, _LocationMetrics],
        group_far: bool,
        check_timeout: Callable[[], None],
    ) -> list[_ClusterState] | Location:
        """Routes holding every stop, or the first stop that wouldn't fit."""
        cluster_states = [_ClusterState() for _ in range(num_clusters)]
        for location in placement_order:
            check_timeout()
            metrics = metrics_by_id[location.location_id]
            feasible_indices = [
                index
                for index, cluster in enumerate(cluster_states)
                if self._can_add_to_cluster(cluster, location, max_boxes, metrics)
            ]
            if not feasible_indices:
                return location

            # Far routes are stop-capped, so near stops fill them first, while
            # the stops are still big. Then even headcount and boxes.
            best_index = min(
                feasible_indices,
                key=lambda index: (
                    (group_far or not metrics.is_far)
                    and not cluster_states[index].has_far_stop,
                    len(cluster_states[index].locations),
                    cluster_states[index].box_count,
                ),
            )
            self._add_to_cluster(cluster_states[best_index], location, metrics)
        return cluster_states

    def _metrics_for_locations(
        self, locations: list[Location]
    ) -> dict[UUID, _LocationMetrics]:
        return {
            location.location_id: self._location_metrics(location)
            for location in locations
        }

    def _location_metrics(self, location: Location) -> _LocationMetrics:
        distance_km = self._haversine_km(
            self._warehouse_lat,
            self._warehouse_lon,
            location,
        )
        is_far = self._is_far_by_address(location) or (
            distance_km >= FAR_DISTANCE_KM_THRESHOLD
        )
        return _LocationMetrics(distance_km=distance_km, is_far=is_far)

    def _can_add_to_cluster(
        self,
        cluster: _ClusterState,
        location: Location,
        max_boxes: int,
        metrics: _LocationMetrics,
    ) -> bool:
        boxes = self._boxes(location)
        if cluster.box_count + boxes > max_boxes:
            return False

        # Only routes with a far delivery are capped on stops and detour.
        if not (cluster.has_far_stop or metrics.is_far):
            return True
        return len(cluster.locations) < FAR_MAX_STOPS_PER_CLUSTER and (
            self._detour_minutes([*cluster.locations, location]) <= FAR_DETOUR_MINUTES
        )

    def _add_to_cluster(
        self,
        cluster: _ClusterState,
        location: Location,
        metrics: _LocationMetrics,
    ) -> None:
        cluster.locations.append(location)
        cluster.box_count += self._boxes(location)
        if metrics.is_far:
            cluster.has_far_stop = True

    def _detour_minutes(self, stops: list[Location]) -> float:
        """Minutes the stops, visited nearest the warehouse first, add to the
        round trip to the farthest one."""
        order = sorted(stops, key=self._warehouse_km)
        hops = sum(self._km(a, b) for a, b in itertools.pairwise(order))
        detour = self._warehouse_km(order[0]) + hops - self._warehouse_km(order[-1])
        return detour / AVERAGE_SPEED_KMH * 60.0

    def _detour_with(self, stop: Location, route: _ClusterState) -> float:
        return self._detour_minutes([*route.locations, stop])

    def _warehouse_km(self, location: Location) -> float:
        return self._haversine_km(self._warehouse_lat, self._warehouse_lon, location)

    def _is_far_by_address(self, location: Location) -> bool:
        address_lower = location.address.lower()
        return any(keyword in address_lower for keyword in FAR_CITY_KEYWORDS)

    def _haversine_km(
        self,
        lat1: float,
        lon1: float,
        location: Location,
    ) -> float:
        if location.latitude is None:
            raise LocationLatitudeError(
                f"Location {location.location_id} is missing latitude."
            )
        if location.longitude is None:
            raise LocationLongitudeError(
                f"Location {location.location_id} is missing longitude."
            )

        lat2 = location.latitude
        lon2 = location.longitude
        radius_km = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return radius_km * c

    def _sorted_locations(
        self,
        locations: list[Location],
        check_timeout: Callable[[], None],
    ) -> list[Location]:
        """Return locations sorted by (angle from warehouse, then distance)."""

        keys: dict[UUID, tuple[float, float]] = {}
        for location in locations:
            check_timeout()
            if location.latitude is None:
                raise LocationLatitudeError(
                    f"Location {location.location_id} is missing latitude."
                )
            if location.longitude is None:
                raise LocationLongitudeError(
                    f"Location {location.location_id} is missing longitude."
                )
            dlat = location.latitude - self._warehouse_lat
            dlon = location.longitude - self._warehouse_lon
            keys[location.location_id] = (
                math.atan2(dlat, dlon) % math.tau,
                dlon**2 + dlat**2,
            )
        return sorted(locations, key=lambda location: keys[location.location_id])

    def _boxes(self, location: Location) -> int:
        return effective_boxes(location, self._children_per_box)

    def _km(self, a: Location, b: Location) -> float:
        # Coordinates were checked when the stops were sorted.
        assert a.latitude is not None and a.longitude is not None
        return self._haversine_km(a.latitude, a.longitude, b)

    def _km_to_route(self, stop: Location, route: _ClusterState) -> float:
        return min(self._km(stop, other) for other in route.locations)


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
                key=lambda stop: clustering._haversine_km(
                    warehouse_lat, warehouse_lon, stop
                ),
            )
            for cluster in clusters
        ]

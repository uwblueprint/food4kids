from __future__ import annotations

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

# Rough drive-time model for balancing.
AVERAGE_SPEED_KMH = 40.0

# Extra minutes on far routes: approximate warehouse round-trip drive allowance.
FAR_ROUND_TRIP_DRIVE_MINUTES = 90.0

# Boxes a sector may run over its car before the extra stops move to a
# neighbour; more just means more stops leave their sector.
SECTOR_OVERFLOW_BOXES = 2


class LocationLatitudeError(Exception):
    """Raised when a location doesn't have a latitude."""

    pass


class LocationLongitudeError(Exception):
    """Raised when a location doesn't have a longitude."""

    pass


class TimeoutError(Exception):
    """Raised when an operation exceeds its timeout limit."""

    pass


def effective_boxes(location: Location, children_per_box: int) -> int:
    """Boxes a location needs: ceil(num_children / children_per_box).

    ``children_per_box`` comes from system settings; the divisor is no longer
    hardcoded. See app.utilities.boxes.compute_boxes.
    """
    return compute_boxes(location.num_children, children_per_box)


@dataclass
class _ClusterState:
    locations: list[Location] = field(default_factory=list)
    stop_count: int = 0
    box_count: int = 0
    has_far_stop: bool = False
    estimated_minutes: float = 0.0


@dataclass(frozen=True)
class _LocationMetrics:
    """Precomputed per-location values used during assignment (avoids repeat haversine)."""

    distance_km: float
    is_far: bool
    stop_minutes: float


class SweepClusteringAlgorithm(ClusteringAlgorithmProtocol):
    """Sweep-line clustering for route generation.

    Capacity is measured in boxes (``max_boxes_per_cluster``). The only stop
    count limit is ``FAR_MAX_STOPS_PER_CLUSTER``, which applies solely to routes
    containing a far delivery and stands in for drive time rather than capacity.
    """

    def __init__(
        self,
        warehouse_lat: float,
        warehouse_lon: float,
        children_per_box: int,
        service_minutes_per_stop: int,
    ) -> None:
        self._warehouse_lat = warehouse_lat
        self._warehouse_lon = warehouse_lon
        self._children_per_box = children_per_box
        self._service_minutes_per_stop = service_minutes_per_stop

    async def cluster_locations(
        self,
        locations: list[Location],
        num_clusters: int,
        max_boxes_per_cluster: int,
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:
        """
        Cluster into exactly ``num_clusters`` routes (one per driver).

        Locations are sweep-sorted from the warehouse and cut into contiguous
        sectors (see ``_sectors``). If no sectoring fits, they are assigned
        greedily to the least-loaded feasible route instead: far stops first,
        then the rest largest-first, so small stops fill the gaps big ones
        leave. That always packs 1- and 2-box stops without far routes when
        they fit; otherwise it is a heuristic and can miss a packing.
        """
        start_time = time.time()

        def check_timeout() -> None:
            if timeout_seconds is not None:
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    raise TimeoutError(
                        f"Route generation exceeded timeout of {timeout_seconds}s "
                        f"(elapsed: {elapsed:.2f}s)"
                    )

        if len(locations) == 0:
            raise ValueError("locations list cannot be empty")
        if num_clusters < 1:
            raise ValueError("num_clusters must be at least 1")

        total_locations = len(locations)
        if num_clusters > total_locations:
            raise ValueError(
                f"Cannot create {num_clusters} clusters: not enough locations"
            )

        for location in locations:
            check_timeout()
            if (
                effective_boxes(location, self._children_per_box)
                > max_boxes_per_cluster
            ):
                raise ValueError(
                    f"Location '{location.name}' requires "
                    f"{effective_boxes(location, self._children_per_box)} boxes, "
                    f"which exceeds the per-driver maximum of {max_boxes_per_cluster}."
                )

        total_boxes = sum(
            effective_boxes(location, self._children_per_box) for location in locations
        )
        if total_boxes > num_clusters * max_boxes_per_cluster:
            raise ValueError(
                f"{total_boxes} boxes need at least "
                f"{math.ceil(total_boxes / max_boxes_per_cluster)} drivers at "
                f"{max_boxes_per_cluster} boxes each, but only {num_clusters} "
                f"were requested."
            )

        sorted_locations = self._sorted_locations(
            locations=locations,
            check_timeout=check_timeout,
        )
        metrics_by_id = self._metrics_for_locations(sorted_locations)

        sectors = self._sectors(
            sorted_locations=sorted_locations,
            num_clusters=num_clusters,
            max_boxes=max_boxes_per_cluster,
            metrics_by_id=metrics_by_id,
            check_timeout=check_timeout,
        )
        clusters = sectors or self._spread(
            sorted_locations=sorted_locations,
            num_clusters=num_clusters,
            max_boxes=max_boxes_per_cluster,
            metrics_by_id=metrics_by_id,
            check_timeout=check_timeout,
        )

        # Defensive: should be unreachable if _can_add_to_cluster stays in sync.
        for index, cluster in enumerate(clusters):
            cluster_boxes = sum(
                effective_boxes(loc, self._children_per_box) for loc in cluster
            )
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
        """Greedy least-loaded assignment, in sweep order within each route."""
        # Quickest first among equals: far routes take the earliest near stops.
        placement_order = sorted(
            sorted_locations,
            key=lambda location: (
                not metrics_by_id[location.location_id].is_far,
                -effective_boxes(location, self._children_per_box),
                metrics_by_id[location.location_id].stop_minutes,
            ),
        )
        # Spreading far stops keeps each far route's box room; grouping them
        # frees stop slots. Neither suits every load, so try both.
        for group_far in (False, True):
            assigned = self._assign(
                placement_order=placement_order,
                num_clusters=num_clusters,
                max_boxes=max_boxes,
                metrics_by_id=metrics_by_id,
                group_far=group_far,
                check_timeout=check_timeout,
            )
            if isinstance(assigned, list):
                break
            unplaced = assigned
        else:
            boxes = effective_boxes(unplaced, self._children_per_box)
            raise ValueError(
                f"Cannot assign '{unplaced.name}' ({boxes} boxes) across {num_clusters} "
                f"drivers: no fit found within max {max_boxes} boxes per "
                f"driver and the far-route caps. Add drivers or adjust loads."
            )

        sweep_rank = {
            location.location_id: rank for rank, location in enumerate(sorted_locations)
        }
        return [
            sorted(
                state.locations, key=lambda location: sweep_rank[location.location_id]
            )
            for state in assigned
        ]

    def _sectors(
        self,
        sorted_locations: list[Location],
        num_clusters: int,
        max_boxes: int,
        metrics_by_id: dict[UUID, _LocationMetrics],
        check_timeout: Callable[[], None],
    ) -> list[list[Location]] | None:
        """Cut the circular sweep into ``num_clusters`` contiguous sectors with
        the fewest boxes over capacity, then the most even stop counts.

        Each sector over capacity hands its smallest stops, nearest its edges,
        to the nearest sectors with room: other sectors' room is mostly single
        boxes. Returns None if no cut, or no
        hand-off, fits.
        """
        n = len(sorted_locations)
        run_limit = max_boxes + SECTOR_OVERFLOW_BOXES  # every stop has a box
        # Overflow outranks evenness: a sum of squared stop counts is <= n^2.
        overflow_weight = n * n + 1
        best: tuple[int, list[Location], list[int]] | None = None
        # Every cut of the circle has a sector boundary within its first
        # run_limit positions, so these rotations cover them all.
        for start in range(min(n, run_limit)):
            sequence = sorted_locations[start:] + sorted_locations[:start]
            # costs[i][length]: sector sequence[i : i + length], if it fits.
            costs: list[list[int]] = []
            for i in range(n):
                check_timeout()
                state, row = _ClusterState(), [0]
                for stop in sequence[i : min(n, i + run_limit)]:
                    metrics = metrics_by_id[stop.location_id]
                    if not self._can_add_to_cluster(state, stop, run_limit, metrics):
                        break
                    self._add_to_cluster(state, stop, metrics)
                    overflow = max(0, state.box_count - max_boxes)
                    row.append(overflow * overflow_weight + state.stop_count**2)
                costs.append(row)

            unreachable = math.inf
            total = [0.0] + [unreachable] * n
            lengths: list[list[int]] = []
            for _ in range(num_clusters):
                check_timeout()
                next_total = [unreachable] * (n + 1)
                next_lengths = [0] * (n + 1)
                for end in range(1, n + 1):
                    for length in range(1, min(run_limit, end) + 1):
                        row = costs[end - length]
                        if length < len(row):
                            candidate = total[end - length] + row[length]
                            if candidate < next_total[end]:
                                next_total[end] = candidate
                                next_lengths[end] = length
                total = next_total
                lengths.append(next_lengths)
            if total[n] == unreachable:
                continue
            if best is None or total[n] < best[0]:
                cuts, end = [], n
                for sector_lengths in reversed(lengths):
                    end -= sector_lengths[end]
                    cuts.append(end)
                best = (int(total[n]), sequence, [*cuts[::-1], n])

        if best is None:
            return None
        _, sequence, cuts = best
        sectors = [_ClusterState() for _ in range(num_clusters)]
        handed_off: list[tuple[int, Location]] = []
        for index, state in enumerate(sectors):
            run = sequence[cuts[index] : cuts[index + 1]]
            overflow = (
                sum(effective_boxes(s, self._children_per_box) for s in run) - max_boxes
            )
            while overflow > 0:
                stop = run.pop(self._hand_off_position(run))
                overflow -= effective_boxes(stop, self._children_per_box)
                handed_off.append((index, stop))
            for stop in run:
                self._add_to_cluster(state, stop, metrics_by_id[stop.location_id])

        for home, stop in handed_off:
            metrics = metrics_by_id[stop.location_id]
            fits = [
                index
                for index, state in enumerate(sectors)
                if self._can_add_to_cluster(state, stop, max_boxes, metrics)
            ]
            if not fits:
                return None

            def distance(index: int, home: int = home) -> int:
                gap = abs(index - home)
                return min(gap, num_clusters - gap)

            self._add_to_cluster(sectors[min(fits, key=distance)], stop, metrics)

        rank = {stop.location_id: position for position, stop in enumerate(sequence)}
        return [
            sorted(state.locations, key=lambda stop: rank[stop.location_id])
            for state in sectors
        ]

    def _hand_off_position(self, run: list[Location]) -> int:
        """The stop to move out of an overfull sector: the smallest, nearest an
        edge so the sector stays contiguous."""
        return min(
            range(len(run)),
            key=lambda i: (
                effective_boxes(run[i], self._children_per_box),
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
        start_time = time.time()

        def check_timeout() -> None:
            if timeout_seconds is not None:
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    raise TimeoutError(
                        f"Route generation exceeded timeout of {timeout_seconds}s "
                        f"(elapsed: {elapsed:.2f}s)"
                    )

        if len(locations) == 0:
            raise ValueError("locations list cannot be empty")

        sorted_locations = self._sorted_locations(
            locations=locations,
            check_timeout=check_timeout,
        )
        metrics_by_id = self._metrics_for_locations(sorted_locations)

        cluster_states: list[_ClusterState] = []
        current = _ClusterState()

        for location in sorted_locations:
            check_timeout()
            metrics = metrics_by_id[location.location_id]

            can_add = self._can_add_to_cluster(
                cluster=current,
                location=location,
                max_boxes=max_boxes_per_cluster,
                metrics=metrics,
            )

            if current.locations and not can_add:
                cluster_states.append(current)
                current = _ClusterState()
                can_add = self._can_add_to_cluster(
                    cluster=current,
                    location=location,
                    max_boxes=max_boxes_per_cluster,
                    metrics=metrics,
                )

            if not can_add:
                boxes = effective_boxes(location, self._children_per_box)
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
                if self._can_add_to_cluster(
                    cluster=cluster,
                    location=location,
                    max_boxes=max_boxes,
                    metrics=metrics,
                )
            ]
            if not feasible_indices:
                return location

            # Far routes are stop-capped, so near stops fill them first, while
            # the stops are still big.
            best_index = min(
                feasible_indices,
                key=lambda index: (
                    (group_far or not metrics.is_far)
                    and not cluster_states[index].has_far_stop,
                    self._cluster_load_key(cluster_states[index]),
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
        drive_minutes = (distance_km / AVERAGE_SPEED_KMH) * 60.0
        stop_minutes = self._service_minutes_per_stop + drive_minutes
        return _LocationMetrics(
            distance_km=distance_km,
            is_far=is_far,
            stop_minutes=stop_minutes,
        )

    def _can_add_to_cluster(
        self,
        cluster: _ClusterState,
        location: Location,
        max_boxes: int,
        metrics: _LocationMetrics,
    ) -> bool:
        boxes = effective_boxes(location, self._children_per_box)
        if cluster.box_count + boxes > max_boxes:
            return False

        stop_cap = self._effective_stop_cap(cluster, metrics.is_far)
        if stop_cap is not None and cluster.stop_count + 1 > stop_cap:
            return False

        far_time_exceeded = (cluster.has_far_stop or metrics.is_far) and (
            cluster.estimated_minutes + metrics.stop_minutes
            > self._far_route_minutes_cap()
        )
        return not far_time_exceeded

    def _add_to_cluster(
        self,
        cluster: _ClusterState,
        location: Location,
        metrics: _LocationMetrics,
    ) -> None:
        cluster.locations.append(location)
        cluster.stop_count += 1
        cluster.box_count += effective_boxes(location, self._children_per_box)
        if metrics.is_far:
            cluster.has_far_stop = True
        cluster.estimated_minutes += metrics.stop_minutes

    def _effective_stop_cap(
        self,
        cluster: _ClusterState,
        location_is_far: bool,
    ) -> int | None:
        """Stops are capped only on routes that include a far delivery."""
        if cluster.has_far_stop or location_is_far:
            return FAR_MAX_STOPS_PER_CLUSTER
        return None

    def _far_route_minutes_cap(self) -> float:
        """Soft time budget for routes that include far deliveries.

        Only ever applied to far routes, whose stop cap is always
        FAR_MAX_STOPS_PER_CLUSTER, so this is a full far route's dwell time
        plus a round-trip drive allowance.
        """
        return (
            FAR_MAX_STOPS_PER_CLUSTER * self._service_minutes_per_stop
            + FAR_ROUND_TRIP_DRIVE_MINUTES
        )

    def _cluster_load_key(self, cluster: _ClusterState) -> tuple[float, float, float]:
        """Lower is better when assigning the next stop.

        Priority: stop count first (even headcount), then boxes, then estimated
        minutes. Stop count is primary because drivers are balanced by number of
        deliveries; box totals can diverge when child counts vary per school.
        """
        return (
            float(cluster.stop_count),
            float(cluster.box_count),
            cluster.estimated_minutes,
        )

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

        def calculate_angle_from_warehouse(location: Location) -> float:
            if location.latitude is None:
                raise LocationLatitudeError(
                    f"Location {location.location_id} is missing latitude."
                )
            if location.longitude is None:
                raise LocationLongitudeError(
                    f"Location {location.location_id} is missing longitude."
                )
            lat_difference = location.latitude - self._warehouse_lat
            lon_difference = location.longitude - self._warehouse_lon
            return math.atan2(lat_difference, lon_difference) % math.tau

        def calculate_distance_squared(location: Location) -> float:
            if location.latitude is None:
                raise LocationLatitudeError(
                    f"Location {location.location_id} is missing latitude."
                )
            if location.longitude is None:
                raise LocationLongitudeError(
                    f"Location {location.location_id} is missing longitude."
                )
            lat_difference = location.latitude - self._warehouse_lat
            lon_difference = location.longitude - self._warehouse_lon
            return lon_difference**2 + lat_difference**2

        locations_with_angles: list[tuple[Location, float, float]] = []
        for location in locations:
            check_timeout()
            angle = calculate_angle_from_warehouse(location)
            distance_squared = calculate_distance_squared(location)
            locations_with_angles.append((location, angle, distance_squared))

        sorted_locations = sorted(
            locations_with_angles, key=lambda item: (item[1], item[2])
        )
        return [location for (location, _angle, _distance) in sorted_locations]


class SweepRoutingAlgorithm:
    """Sweep clustering as a complete routing engine, at no API cost.

    Each cluster is already in sweep order (angle, then distance from the
    warehouse), so it doubles as the visit order.
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
            service_minutes_per_stop=settings.service_time_minutes,
        )
        return await clustering.cluster_locations(
            locations=locations,
            num_clusters=settings.num_routes,
            max_boxes_per_cluster=settings.max_boxes_per_driver,
            timeout_seconds=timeout_seconds,
        )

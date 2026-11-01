from __future__ import annotations

import itertools
import math
import time
from dataclasses import dataclass, field, replace
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

# How many routes deep one repair may chain: making room for a stop moves stops
# off one route, and placing those may move stops off another.
REPAIR_DEPTH = 2


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

        Locations are sweep-sorted from the warehouse, then assigned greedily
        to the least-loaded feasible route so work is spread evenly while
        respecting box and far-delivery limits. When no route has room, a
        repair moves stops between routes to make some (see ``_place``).
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

        # Far stops first: a far route caps at FAR_MAX_STOPS_PER_CLUSTER stops,
        # so one arriving late in the sweep would find no route short enough.
        placement_order = sorted(
            sorted_locations,
            key=lambda location: not metrics_by_id[location.location_id].is_far,
        )
        # One far stop per route keeps each far route's box room; sharing
        # routes frees stop slots. Neither suits every load, so try both.
        has_far = any(metrics.is_far for metrics in metrics_by_id.values())
        for consolidate_far in (False, True) if has_far else (False,):
            assigned = self._assign(
                placement_order=placement_order,
                num_clusters=num_clusters,
                max_boxes=max_boxes_per_cluster,
                metrics_by_id=metrics_by_id,
                consolidate_far=consolidate_far,
                check_timeout=check_timeout,
            )
            if isinstance(assigned, list):
                break
            unplaced = assigned
        else:
            boxes = effective_boxes(unplaced, self._children_per_box)
            raise ValueError(
                f"Cannot assign '{unplaced.name}' ({boxes} boxes) across {num_clusters} "
                f"drivers: no arrangement found fits every stop within max "
                f"{max_boxes_per_cluster} boxes per driver and the far-route caps "
                f"({FAR_MAX_STOPS_PER_CLUSTER} stops, "
                f"{self._far_route_minutes_cap():.0f} minutes). Add drivers or "
                f"adjust loads."
            )

        # Repairs move stops between routes; restore the sweep (visit) order.
        sweep_rank = {
            location.location_id: rank for rank, location in enumerate(sorted_locations)
        }
        clusters = [
            sorted(
                state.locations, key=lambda location: sweep_rank[location.location_id]
            )
            for state in assigned
        ]

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
        consolidate_far: bool,
        check_timeout: Callable[[], None],
    ) -> list[_ClusterState] | Location:
        """Routes holding every stop, or the first stop that wouldn't fit."""
        clusters = [_ClusterState() for _ in range(num_clusters)]

        def place(location: Location) -> bool:
            return self._place(
                location=location,
                clusters=clusters,
                max_boxes=max_boxes,
                metrics_by_id=metrics_by_id,
                depth=REPAIR_DEPTH,
                consolidate_far=consolidate_far,
                check_timeout=check_timeout,
            )

        for location in placement_order:
            check_timeout()
            placed = place(location) or (
                self._compact_far_routes(
                    clusters, max_boxes, metrics_by_id, check_timeout
                )
                and place(location)
            )
            if not placed:
                return location
        return clusters

    def _place(
        self,
        location: Location,
        clusters: list[_ClusterState],
        max_boxes: int,
        metrics_by_id: dict[UUID, _LocationMetrics],
        depth: int,
        consolidate_far: bool,
        check_timeout: Callable[[], None],
    ) -> bool:
        """Add ``location`` to the least-loaded route it fits on (for a far
        stop with ``consolidate_far``, preferring routes that already have one).

        If none has room, make room on one by moving one or two of its smaller
        stops elsewhere, each placed the same way with ``depth - 1``. Returns
        False, leaving ``clusters`` unchanged, if nothing works.
        """
        metrics = metrics_by_id[location.location_id]
        feasible_indices = [
            index
            for index, cluster in enumerate(clusters)
            if self._can_add_to_cluster(cluster, location, max_boxes, metrics)
        ]
        if feasible_indices:
            best_index = min(
                feasible_indices,
                key=lambda index: (
                    consolidate_far
                    and metrics.is_far
                    and not clusters[index].has_far_stop,
                    self._cluster_load_key(clusters[index]),
                ),
            )
            clusters[best_index] = self._cluster_with(
                clusters[best_index], location, metrics
            )
            return True

        if depth == 0:
            return False

        # Least-loaded routes first: they need the fewest stops moved off.
        targets = sorted(
            range(len(clusters)),
            key=lambda index: self._cluster_load_key(clusters[index]),
        )
        for index in targets:
            for ejected in self._ejection_sets(
                clusters[index], location, max_boxes, metrics_by_id
            ):
                check_timeout()
                snapshot = list(clusters)
                clusters[index] = self._cluster_with(
                    self._cluster_without(clusters[index], ejected, metrics_by_id),
                    location,
                    metrics,
                )
                if all(
                    self._place(
                        location=stop,
                        clusters=clusters,
                        max_boxes=max_boxes,
                        metrics_by_id=metrics_by_id,
                        depth=depth - 1,
                        consolidate_far=consolidate_far,
                        check_timeout=check_timeout,
                    )
                    for stop in ejected
                ):
                    return True
                clusters[:] = snapshot
        return False

    def _compact_far_routes(
        self,
        clusters: list[_ClusterState],
        max_boxes: int,
        metrics_by_id: dict[UUID, _LocationMetrics],
        check_timeout: Callable[[], None],
    ) -> bool:
        """Swap near stops onto far routes that are bigger or quicker than theirs.

        Far routes fill up on stops and minutes before boxes, so their room is
        best spent on big, quick stops; this frees boxes on the other routes.
        Every swap improves one far route and leaves the others' caps alone,
        so it terminates. Returns whether anything moved.
        """
        moved = False
        improved = True
        while improved:
            improved = False
            for far_index, far_route in enumerate(clusters):
                if not far_route.has_far_stop:
                    continue
                for index, route in enumerate(clusters):
                    if route.has_far_stop:
                        continue
                    check_timeout()
                    swap = self._best_far_swap(
                        far_route, route, max_boxes, metrics_by_id
                    )
                    if swap is None:
                        continue
                    outgoing, incoming = swap
                    far_route = self._cluster_with(
                        self._cluster_without(far_route, (outgoing,), metrics_by_id),
                        incoming,
                        metrics_by_id[incoming.location_id],
                    )
                    clusters[far_index] = far_route
                    clusters[index] = self._cluster_with(
                        self._cluster_without(route, (incoming,), metrics_by_id),
                        outgoing,
                        metrics_by_id[outgoing.location_id],
                    )
                    moved = improved = True
        return moved

    def _best_far_swap(
        self,
        far_route: _ClusterState,
        route: _ClusterState,
        max_boxes: int,
        metrics_by_id: dict[UUID, _LocationMetrics],
    ) -> tuple[Location, Location] | None:
        """The (outgoing, incoming) near-stop swap that most improves
        ``far_route``: more boxes first, then fewer minutes."""

        def value(stop: Location) -> tuple[int, float]:
            return (
                effective_boxes(stop, self._children_per_box),
                -metrics_by_id[stop.location_id].stop_minutes,
            )

        best: tuple[Location, Location] | None = None
        best_gain = (0, 0.0)
        for outgoing in far_route.locations:
            if metrics_by_id[outgoing.location_id].is_far:
                continue
            remaining = self._cluster_without(far_route, (outgoing,), metrics_by_id)
            outgoing_boxes, outgoing_minutes = value(outgoing)
            for incoming in route.locations:
                incoming_boxes, incoming_minutes = value(incoming)
                gain = (
                    incoming_boxes - outgoing_boxes,
                    incoming_minutes - outgoing_minutes,
                )
                # Boxes never drop on the far route, so ``route`` stays in cap.
                if incoming_boxes < outgoing_boxes or gain <= best_gain:
                    continue
                if self._can_add_to_cluster(
                    remaining, incoming, max_boxes, metrics_by_id[incoming.location_id]
                ):
                    best, best_gain = (outgoing, incoming), gain
        return best

    def _ejection_sets(
        self,
        cluster: _ClusterState,
        location: Location,
        max_boxes: int,
        metrics_by_id: dict[UUID, _LocationMetrics],
    ) -> list[tuple[Location, ...]]:
        """One or two of ``cluster``'s stops whose removal lets ``location`` in,
        fewest and smallest first.

        Only stops with fewer boxes than ``location`` qualify, so box counts
        shrink down every chain; trades of equal size are only ever worth it
        on far routes, which ``_compact_far_routes`` handles.
        """
        boxes = effective_boxes(location, self._children_per_box)
        smaller = [
            stop
            for stop in cluster.locations
            if effective_boxes(stop, self._children_per_box) < boxes
        ]
        candidates: list[tuple[Location, ...]] = [(stop,) for stop in smaller]
        candidates += list(itertools.combinations(smaller, 2))
        metrics = metrics_by_id[location.location_id]
        fitting = [
            ejected
            for ejected in candidates
            if self._can_add_to_cluster(
                self._cluster_without(cluster, ejected, metrics_by_id),
                location,
                max_boxes,
                metrics,
            )
        ]
        return sorted(
            fitting,
            key=lambda ejected: (
                len(ejected),
                sum(effective_boxes(stop, self._children_per_box) for stop in ejected),
            ),
        )

    def _cluster_without(
        self,
        cluster: _ClusterState,
        removed: tuple[Location, ...],
        metrics_by_id: dict[UUID, _LocationMetrics],
    ) -> _ClusterState:
        """Rebuilt rather than decremented, so totals match a fresh build exactly."""
        removed_ids = {stop.location_id for stop in removed}
        rebuilt = _ClusterState()
        for stop in cluster.locations:
            if stop.location_id not in removed_ids:
                self._add_to_cluster(rebuilt, stop, metrics_by_id[stop.location_id])
        return rebuilt

    def _cluster_with(
        self,
        cluster: _ClusterState,
        location: Location,
        metrics: _LocationMetrics,
    ) -> _ClusterState:
        """A copy plus ``location``; repairs never mutate a route in place, so
        undoing one is restoring the list of routes."""
        extended = replace(cluster, locations=list(cluster.locations))
        self._add_to_cluster(extended, location, metrics)
        return extended

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

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.services.protocols.clustering_algorithm import ClusteringAlgorithmProtocol

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

    from app.models.location import Location


DEFAULT_MAX_BOXES_PER_CLUSTER = 14

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

# Rough drive-time model for balancing (minutes).
DEFAULT_SERVICE_MINUTES_PER_STOP = 15
AVERAGE_SPEED_KMH = 40.0

# Extra minutes on far routes: approximate warehouse round-trip drive allowance.
FAR_ROUND_TRIP_DRIVE_MINUTES = 90.0


class LocationLatitudeError(Exception):
    """Raised when a location doesn't have a latitude."""

    pass


class LocationLongitudeError(Exception):
    """Raised when a location doesn't have a longitude."""

    pass


class TimeoutError(Exception):
    """Raised when an operation exceeds its timeout limit."""

    pass


def effective_boxes(location: Location) -> int:
    """Box count = ceil(children / 2); fall back to stored num_boxes."""
    if location.num_children is not None and location.num_children > 0:
        return math.ceil(location.num_children / 2)
    return max(location.num_boxes, 0)


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

    Enforces both ``max_locations_per_cluster`` and ``max_boxes_per_cluster`` when
    provided (same as ``MockClusteringAlgorithm``). The protocol allows
    implementations to require at most one limit; this class applies both for F4K
    driver rules (stops, boxes, and far-route caps).
    """

    def __init__(self, warehouse_lat: float, warehouse_lon: float) -> None:
        self._warehouse_lat = warehouse_lat
        self._warehouse_lon = warehouse_lon

    async def cluster_locations(
        self,
        locations: list[Location],
        num_clusters: int,
        max_locations_per_cluster: int | None = None,
        max_boxes_per_cluster: int | None = None,
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:
        """
        Cluster into exactly ``num_clusters`` routes (one per driver).

        Locations are sweep-sorted from the warehouse, then assigned greedily
        to the least-loaded feasible route so work is spread evenly while
        respecting box, stop, and far-delivery limits. Both max stop and max box
        limits apply together when both arguments are set.
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

        max_boxes = (
            max_boxes_per_cluster
            if max_boxes_per_cluster is not None
            else DEFAULT_MAX_BOXES_PER_CLUSTER
        )

        for location in locations:
            check_timeout()
            if effective_boxes(location) > max_boxes:
                name = location.school_name or location.contact_name
                raise ValueError(
                    f"Location '{name}' requires {effective_boxes(location)} boxes, "
                    f"which exceeds the per-driver maximum of {max_boxes}."
                )

        sorted_locations = self._sorted_locations(
            locations=locations,
            check_timeout=check_timeout,
        )
        metrics_by_id = self._metrics_for_locations(sorted_locations)

        cluster_states = [_ClusterState() for _ in range(num_clusters)]

        for location in sorted_locations:
            check_timeout()
            metrics = metrics_by_id[location.location_id]
            feasible_indices = [
                index
                for index, cluster in enumerate(cluster_states)
                if self._can_add_to_cluster(
                    cluster=cluster,
                    location=location,
                    max_boxes=max_boxes,
                    max_stops=max_locations_per_cluster,
                    metrics=metrics,
                )
            ]

            if not feasible_indices:
                name = location.school_name or location.contact_name
                boxes = effective_boxes(location)
                raise ValueError(
                    f"Cannot assign '{name}' ({boxes} boxes) across {num_clusters} "
                    f"drivers without violating max {max_boxes} boxes per driver, "
                    f"stop limits, or far-route caps. Add drivers or adjust loads."
                )

            best_index = min(
                feasible_indices,
                key=lambda index: self._cluster_load_key(cluster_states[index]),
            )
            self._add_to_cluster(cluster_states[best_index], location, metrics)

        clusters = [state.locations for state in cluster_states]

        # Defensive: should be unreachable if _can_add_to_cluster stays in sync.
        for index, cluster in enumerate(clusters):
            if (
                max_locations_per_cluster is not None
                and len(cluster) > max_locations_per_cluster
            ):
                raise ValueError(
                    f"Cluster {index + 1} would have {len(cluster)} locations, "
                    f"exceeding max_locations_per_cluster={max_locations_per_cluster}."
                )
            cluster_boxes = sum(effective_boxes(loc) for loc in cluster)
            if cluster_boxes > max_boxes:
                raise ValueError(
                    f"Cluster {index + 1} would have {cluster_boxes} boxes, "
                    f"exceeding max_boxes_per_cluster={max_boxes}."
                )

        return clusters

    async def cluster_locations_by_constraints(
        self,
        locations: list[Location],
        max_locations_per_cluster: int | None = None,
        max_boxes_per_cluster: int | None = None,
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

        max_boxes = (
            max_boxes_per_cluster
            if max_boxes_per_cluster is not None
            else DEFAULT_MAX_BOXES_PER_CLUSTER
        )

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
                max_boxes=max_boxes,
                max_stops=max_locations_per_cluster,
                metrics=metrics,
            )

            if current.locations and not can_add:
                cluster_states.append(current)
                current = _ClusterState()
                can_add = self._can_add_to_cluster(
                    cluster=current,
                    location=location,
                    max_boxes=max_boxes,
                    max_stops=max_locations_per_cluster,
                    metrics=metrics,
                )

            if not can_add:
                name = location.school_name or location.contact_name
                raise ValueError(
                    f"Cannot pack location '{name}' ({effective_boxes(location)} boxes) "
                    f"within max {max_boxes} boxes per route."
                )

            self._add_to_cluster(current, location, metrics)

        if current.locations:
            cluster_states.append(current)

        return [state.locations for state in cluster_states]

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
        stop_minutes = DEFAULT_SERVICE_MINUTES_PER_STOP + drive_minutes
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
        max_stops: int | None,
        metrics: _LocationMetrics,
    ) -> bool:
        boxes = effective_boxes(location)
        if cluster.box_count + boxes > max_boxes:
            return False

        stop_cap = self._effective_stop_cap(cluster, metrics.is_far, max_stops)
        if stop_cap is not None and cluster.stop_count + 1 > stop_cap:
            return False

        far_time_exceeded = (cluster.has_far_stop or metrics.is_far) and (
            cluster.estimated_minutes + metrics.stop_minutes
            > self._far_route_minutes_cap(stop_cap)
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
        cluster.box_count += effective_boxes(location)
        if metrics.is_far:
            cluster.has_far_stop = True
        cluster.estimated_minutes += metrics.stop_minutes

    def _effective_stop_cap(
        self,
        cluster: _ClusterState,
        location_is_far: bool,
        max_stops: int | None,
    ) -> int | None:
        if max_stops is None:
            if cluster.has_far_stop or location_is_far:
                return FAR_MAX_STOPS_PER_CLUSTER
            return None
        if cluster.has_far_stop or location_is_far:
            return min(max_stops, FAR_MAX_STOPS_PER_CLUSTER)
        return max_stops

    def _far_route_minutes_cap(self, stop_cap: int | None) -> float:
        """Soft time budget for routes that include far deliveries."""
        stops = stop_cap if stop_cap is not None else FAR_MAX_STOPS_PER_CLUSTER
        return stops * DEFAULT_SERVICE_MINUTES_PER_STOP + FAR_ROUND_TRIP_DRIVE_MINUTES

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

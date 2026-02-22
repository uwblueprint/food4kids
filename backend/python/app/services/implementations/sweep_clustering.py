from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

from app.services.protocols.clustering_algorithm import ClusteringAlgorithmProtocol

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.models.location import Location


class LocationLatitudeError(Exception):
    """Raised when a location doesn't have a latitude."""

    pass


class LocationLongitudeError(Exception):
    """Raised when a location doesn't have a longitude."""

    pass


class TimeoutError(Exception):
    """Raised when an operation exceeds its timeout limit."""

    pass


class SweepClusteringAlgorithm(ClusteringAlgorithmProtocol):
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
        Cluster locations into EXACTLY `num_clusters` clusters, using sweep ordering.

        This is the protocol/contract method: num_clusters is respected.
        Raises ValueError if constraints cannot be satisfied.
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

        base_cluster_size = total_locations // num_clusters
        remainder = total_locations % num_clusters
        max_cluster_size = base_cluster_size + (1 if remainder > 0 else 0)
        if (
            max_locations_per_cluster is not None
            and max_cluster_size > max_locations_per_cluster
        ):
            raise ValueError(
                f"Cannot create {num_clusters} clusters with max "
                f"{max_locations_per_cluster} locations per cluster. "
                f"Required cluster size would be up to {max_cluster_size}."
            )

        sorted_only_locations = self._sorted_locations(
            locations=locations,
            check_timeout=check_timeout,
        )

        clusters: list[list[Location]] = []
        start_index = 0

        for i in range(num_clusters):
            check_timeout()

            size = base_cluster_size + (1 if i < remainder else 0)
            end_index = start_index + size
            cluster = sorted_only_locations[start_index:end_index]
            start_index = end_index

            if (
                max_locations_per_cluster is not None
                and len(cluster) > max_locations_per_cluster
            ):
                raise ValueError(
                    f"Cluster {i + 1} would have {len(cluster)} locations, "
                    f"exceeding max_locations_per_cluster={max_locations_per_cluster}."
                )

            if max_boxes_per_cluster is not None:
                cluster_boxes = sum(loc.num_boxes for loc in cluster)
                if cluster_boxes > max_boxes_per_cluster:
                    raise ValueError(
                        f"Cluster {i + 1} would have {cluster_boxes} boxes, "
                        f"exceeding max_boxes_per_cluster={max_boxes_per_cluster}."
                    )

            clusters.append(cluster)

        if start_index != total_locations:
            raise RuntimeError(
                f"Internal error: assigned {start_index} of {total_locations} locations."
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
        Cluster locations using sweep ordering, greedily packing clusters until
        a constraint is exceeded, then starting a new cluster.

        This prioritizes constraints (max locations / max boxes). It does not
        aim to return a specific number of clusters.
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

        sorted_only_locations = self._sorted_locations(
            locations=locations,
            check_timeout=check_timeout,
        )

        clusters: list[list[Location]] = []
        current_cluster: list[Location] = []
        current_location_count = 0
        current_box_count = 0

        for loc in sorted_only_locations:
            check_timeout()

            would_exceed_locations = (
                max_locations_per_cluster is not None
                and current_location_count + 1 > max_locations_per_cluster
            )
            would_exceed_boxes = (
                max_boxes_per_cluster is not None
                and current_box_count + loc.num_boxes > max_boxes_per_cluster
            )

            if current_cluster and (would_exceed_locations or would_exceed_boxes):
                clusters.append(current_cluster)
                current_cluster = []
                current_location_count = 0
                current_box_count = 0

            current_cluster.append(loc)
            current_location_count += 1
            current_box_count += loc.num_boxes

        if current_cluster:
            clusters.append(current_cluster)

        return clusters

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

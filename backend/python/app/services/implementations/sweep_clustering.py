from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

from app.services.protocols.clustering_algorithm import (
    ClusteringAlgorithmProtocol,
)

if TYPE_CHECKING:
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
    """Simple mock clustering algorithm that splits locations into clusters.

    This is a pure function with no database interaction. It distributes
    locations across clusters while respecting max_locations_per_cluster and
    max_boxes_per_cluster constraints.
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
        """Split locations into clusters while respecting box constraints.

        Args:
            locations: List of locations to cluster
            num_clusters: Target number of clusters to create
            max_locations_per_cluster: Optional maximum number of locations
                per cluster. If provided, validates that the clustering is
                possible and raises an error if violated.
            max_boxes_per_cluster: Optional maximum number of boxes per cluster.
                If provided, validates that the clustering is possible and
                raises an error if violated.
            timeout_seconds: Optional timeout in seconds. Not enforced in this
                mock implementation.

        Returns:
            List of clusters, where each cluster is a list of locations

        Raises:
            ValueError: If the clustering parameters are invalid or cannot
                be satisfied
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

        if len(locations) == 0:
            raise ValueError("locations list cannot be empty")

        if num_clusters < 1:
            raise ValueError("num_clusters must be at least 1")

        # Calculate base cluster size and validate constraints
        total_locations = len(locations)
        base_cluster_size = total_locations // num_clusters
        remainder = total_locations % num_clusters

        if base_cluster_size == 0:
            raise ValueError(
                f"Cannot create {num_clusters} clusters: not enough locations"
            )

        # The largest cluster will have base_cluster_size + 1 if remainder > 0
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

        # Distribute locations while respecting constraints
        clusters: list[list[Location]] = []
        current_location_count = 0
        current_box_count = 0
        current_cluster: list[Location] = []

        locations_with_angles: list[tuple[Location, float, float]] = []
        for location in locations:
            check_timeout()
            angle = calculate_angle_from_warehouse(location)
            distance_squared = calculate_distance_squared(location)
            locations_with_angles.append((location, angle, distance_squared))

        sorted_locations = sorted(
            locations_with_angles, key=lambda location: (location[1], location[2])
        )

        for loc, _angle, _distance in sorted_locations:
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

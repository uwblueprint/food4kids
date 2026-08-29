from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import TYPE_CHECKING

import numpy as np
from sklearn.cluster import KMeans  # type: ignore[import-untyped]

from app.services.protocols.clustering_algorithm import (
    ClusteringAlgorithmProtocol,
)
from app.utilities.boxes import compute_boxes

if TYPE_CHECKING:
    from app.models.location import Location


class KMeansClusteringAlgorithm(ClusteringAlgorithmProtocol):
    """K means clustering algorithm that splits locations into clusters following k means clustering algorithm.

    Includes max boxes per cluster handling via "greedy-esque algorithm"
    """

    def __init__(self, children_per_box: int) -> None:
        self._children_per_box = children_per_box

    async def cluster_locations(
        self,
        locations: list[Location],
        num_clusters: int,
        max_boxes_per_cluster: int,
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:
        return await asyncio.to_thread(
            self._cluster_locations_sync,
            locations,
            num_clusters,
            max_boxes_per_cluster,
            timeout_seconds,
        )

    def _cluster_locations_sync(
        self,
        locations: list[Location],
        num_clusters: int,
        max_boxes_per_cluster: int,
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:
        # If either num_clusters or max_boxes_per_cluster is negative (or equal to 0) raise an error
        if num_clusters <= 0 or max_boxes_per_cluster <= 0:
            raise ValueError(
                "One of the given num_clusters and max_boxes_per_cluster param values given to the algorithm is <= 0 (invalid)"
            )

        # If no locations to cluster, return empty list
        if not locations:
            return [[] for _ in range(num_clusters)]

        # Extract lat and long coords into a numpy array
        coordinates = np.array(
            [[location.latitude, location.longitude] for location in locations]
        )

        # Check if it is mathematically possible to meet the constraints on num of clusters + max boxes per cluster
        total_boxes = sum(
            compute_boxes(loc.num_children, self._children_per_box) for loc in locations
        )

        max_possible = num_clusters * max_boxes_per_cluster

        if total_boxes > max_possible:
            raise ValueError(
                "Max boxes per cluster + number of clusters clustering parameters cannot be simultaneously satisfied"
            )

        try:
            # Run with timeout
            start_time = time.time()

            # kmeans!
            kmeans = KMeans(
                n_clusters=num_clusters,
                random_state=42,
                n_init=10,
            )
            kmeans.fit(coordinates)

            # Distance matrix representing the distance from each point to each centroid
            distances = kmeans.transform(coordinates)
            clusters = self._assign_with_constraints(
                locations,
                distances,
                num_clusters,
                max_boxes_per_cluster,
                start_time,
                timeout_seconds,
            )

            # Check time elapsed
            elapsed = time.time() - start_time
            print("Time:", elapsed)
            if timeout_seconds is not None and elapsed > timeout_seconds:
                raise TimeoutError("K-Means clustering algorithm timed out")

            return clusters
        except TimeoutError:
            # Let callers handle explicit timeouts
            raise
        except Exception as e:
            print(f"Constrained k-means clustering failed: {e}")
            return []

    def _assign_with_constraints(
        self,
        locations: list[Location],
        distances: np.ndarray,
        num_clusters: int,
        max_boxes_per_cluster: int,
        start_time: float,
        timeout_seconds: float | None,
    ) -> list[list[Location]]:
        """
        Assign locations to clusters respecting the box capacity constraint
        Greedy approach: assign closest points first

        Args:
            locations: List of locations to cluster
            distances: Distance matrix between each location and the clusters
            num_clusters: Target number of clusters to create
            max_boxes_per_cluster: Maximum number of boxes per cluster. If it
                cannot be satisfied with the given number of clusters, the
                algorithm raises an error.
            start_time: Time the algorithm began running. Used for timekeeping
                purposes to ensure time limit is not exceeded (and to ensure
                proper handling when the time limit is exceeded)
            timeout_seconds: Optional timeout in seconds. If provided, the
                algorithm should raise TimeoutError if execution exceeds this
                duration. If None, no timeout is enforced.

        Returns:
            List of clusters, where each cluster is a list of locations

        Raises:
            ValueError: If the clustering parameters are invalid or cannot
                be satisfied
            TimeoutError: If a timeout limit is provided and execution exceeds
                this duration.
        """
        # Count number of boxes assigned to each cluster
        cluster_counts: dict[int, int] = defaultdict(int)

        # Hold actual location cluster assignments (None until assigned)
        assignments: list[int | None] = [None] * len(locations)

        # Build candidate list: (location_index, preferred_cluster (by cluster number), distance_to_preferred, all_distances)
        candidates = []
        for i in range(len(locations)):
            best_cluster = int(np.argmin(distances[i]))
            best_distance = distances[i][best_cluster]
            candidates.append((i, best_cluster, best_distance, distances[i]))

        # Sort by distance (closest first)
        candidates.sort(key=lambda x: x[2])

        # Helper to check if we can place a location into a cluster w.r.t. the box cap + place it if yes
        def can_place_and_put(location_index: int, cluster_id: int) -> bool:
            # Look at each cluster, see if num of boxes assigned to that cluster is still within max limit
            # Because using defaultdict, "not-yet-touched" clusters have num boxes = 0 by default
            loc = locations[location_index]
            need = compute_boxes(loc.num_children, self._children_per_box)
            if cluster_counts[cluster_id] + need <= max_boxes_per_cluster:
                assignments[location_index] = cluster_id
                cluster_counts[cluster_id] += need
                return True
            return False

        # Assign each location "greedily" - assign location to closest cluster with space
        for (
            location_index,
            preferred_cluster,
            _distance_to_preferred,
            all_distances,
        ) in candidates:
            # Check runtime and timeout if needed
            if timeout_seconds is not None:
                now = time.time()
                if now - start_time > timeout_seconds:
                    raise TimeoutError("K-Means assignment step timed out")

            # Try the location's preferred cluster first
            if can_place_and_put(location_index, preferred_cluster):
                continue

            sorted_clusters = np.argsort(all_distances)
            placed = False
            # Try other clusters
            for cluster_id in sorted_clusters:
                # Check runtime and timeout if needed
                if timeout_seconds is not None:
                    now = time.time()
                    if now - start_time > timeout_seconds:
                        raise TimeoutError("K-Means assignment step timed out")

                cluster_id = int(cluster_id)
                if can_place_and_put(location_index, cluster_id):
                    placed = True
                    break

            if not placed:
                raise ValueError(
                    f"Unable to assign location index {location_index} under constraints"
                )

        # Build result lists (each list corresponds to locations in a different cluster)
        clusters: list[list[Location]] = [[] for _ in range(num_clusters)]
        for i, location in enumerate(locations):
            cluster_id = assignments[i]
            if cluster_id is not None:
                clusters[cluster_id].append(location)

        return clusters

from __future__ import annotations

import time
from collections import defaultdict
from typing import TYPE_CHECKING

import numpy as np
from sklearn.cluster import KMeans  # type: ignore[import-untyped]

from app.services.protocols.clustering_algorithm import (
    ClusteringAlgorithmProtocol,
)

if TYPE_CHECKING:
    from app.models.location import Location


class KMeansClusteringAlgorithm(ClusteringAlgorithmProtocol):
    """K means clustering algorithm that splits locations into clusters following k means clustering algorithm.

    Includes max locations per cluster handling via "greedy-esque algorithm"
    """

    def cluster_locations(
        self,
        locations: list[Location],
        num_clusters: int,
        max_locations_per_cluster: int | None = None,
        max_boxes_per_cluster: int | None = None,
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:
        """Split locations evenly into clusters in sequential order.

        Args:
            locations: List of locations to cluster
            num_clusters: Target number of clusters to create
            max_locations_per_cluster: Maximum number of locations
                per cluster. Validates that the clustering is
                possible and raises an error if violated
            timeout_seconds: Raise an error if it takes longer than
                timeout_seconds to run the algorithm

        Returns:
            List of clusters, where each cluster is a list of locations

        Raises:
            ValueError: If the clustering parameters are invalid or cannot
                be satisfied
        """
        # Assert that only one AT MOST of the limiting max params is set to a value
        assert max_boxes_per_cluster is None or max_locations_per_cluster is None

        # If any of num_clusters, max_locations_per_cluster, or max_boxes_per_cluster is negative (or equal to 0) raise an error
        if (
            num_clusters <= 0
            or (max_locations_per_cluster and max_locations_per_cluster <= 0)
            or (max_boxes_per_cluster and max_boxes_per_cluster <= 0)
        ):
            raise ValueError(
                "At least one of the given num_clusters, max_locations_per_cluster, and max_boxes_per_cluster param values given to the algorithm is <= 0 (invalid)"
            )

        # If no locations to cluster, return empty list
        if not locations:
            return [[] for _ in range(num_clusters)]

        # Extract lat and long coords into a numpy array
        coordinates = np.array(
            [[location.latitude, location.longitude] for location in locations]
        )

        # Check that clustering is possible for the given locations
        if max_locations_per_cluster is not None:
            # Check if it is mathematically possible to meet the constraints on num of clusters + max locations per cluster
            total_locations = len(locations)
            max_possible = num_clusters * max_locations_per_cluster

            if total_locations > max_possible:
                raise ValueError(
                    "Max locations per cluster + number of clusters clustering parameters cannot be simultaneously satisfied"
                )
        if max_boxes_per_cluster is not None:
            # Check if it is mathematically possible to meet the constraints on num of clusters + max boxes per cluster
            total_boxes = sum(loc.num_boxes for loc in locations)

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

            if (
                max_locations_per_cluster is not None
                or max_boxes_per_cluster is not None
            ):
                # Distance matrix representing the distance from each point to each centroid
                distances = kmeans.transform(coordinates)
                clusters = self._assign_with_constraints(
                    locations,
                    distances,
                    num_clusters,
                    max_locations_per_cluster,
                    max_boxes_per_cluster,
                    start_time,
                    timeout_seconds,
                )
            else:
                # No constraints
                cluster_labels = kmeans.predict(coordinates)

                # Build result lists (each list corresponds to locations in a different cluster)
                clusters = [[] for _ in range(num_clusters)]
                for i, location in enumerate(locations):
                    cluster_id = int(cluster_labels[i])
                    clusters[cluster_id].append(location)

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
        max_locations_per_cluster: int | None,
        max_boxes_per_cluster: int | None,
        start_time: float,
        timeout_seconds: float | None,
    ) -> list[list[Location]]:
        """
        Assign locations to clusters respecting size constraints
        Greedy approach: assign closest points first
        """
        # Assert that only one AT MOST of the limiting max params is set to a value
        assert max_boxes_per_cluster is None or max_locations_per_cluster is None

        # Count number of locations in each cluster
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

        # Helper to check if we can place a location into a cluster w.r.t. constraints + place it if yes
        def can_place_and_put(location_index: int, cluster_id: int) -> bool:
            # Look at each cluster, see if num of locations or num of boxes (depending on constraints) assigned to that cluster is still within max limit
            # Because using defaultdict, "not-yet-touched" clusters have num locations/boxes = 0 by default
            loc = locations[location_index]
            if max_locations_per_cluster is not None:
                # Count location
                need = 1
                if cluster_counts[cluster_id] + need <= max_locations_per_cluster:
                    assignments[location_index] = cluster_id
                    cluster_counts[cluster_id] += need
                    return True
                return False

            # Otherwise boxes constraint must be active (by assert)
            if max_boxes_per_cluster is not None:
                # Count boxes at location
                need = getattr(loc, "num_boxes", 0)
                if cluster_counts[cluster_id] + need <= max_boxes_per_cluster:
                    assignments[location_index] = cluster_id
                    cluster_counts[cluster_id] += need
                    return True
                return False

            # If no constraints, always allow placement (should never run this function if there are no constraints, but added for mypy's happiness!)
            return True

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

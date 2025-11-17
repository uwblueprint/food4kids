from __future__ import annotations
import numpy as np
import math
import time
from sklearn.cluster import KMeans
from collections import defaultdict
from typing import TYPE_CHECKING

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
        timeout_seconds: float | None = None,  # noqa: ARG002
    ) -> list[list[Location]]:
        """Split locations evenly into clusters in sequential order.

        Args:
            locations: List of locations to cluster
            num_clusters: Target number of clusters to create
            max_locations_per_cluster: Maximum number of locations
                per cluster. Validates that the clustering is
                possible and raises an error if violated.
            timeout_seconds: Optional timeout in seconds. Not enforced in this
                mock implementation.

        Returns:
            List of clusters, where each cluster is a list of locations

        Raises:
            ValueError: If the clustering parameters are invalid or cannot
                be satisfied
        """
        # Assert that only one AT MOST of the limiting max params is set to a value
        assert max_boxes_per_cluster is None or max_locations_per_cluster is None

        # If no locations to cluster, return empty list
        if not locations:
            return [[] for _ in range(num_clusters)]
        
        # Extract lat and long coords into a numpy array
        coordinates = np.array([[location.latitude, location.longitude] for location in locations])

        # Check that clustering is possible for the given locations
        if max_locations_per_cluster is not None:
            # Check if it is mathematically possible to meet the constraints on num of clusters + max locations per cluster
            total_locations = len(locations)
            max_possible = num_clusters * max_locations_per_cluster

            if total_locations > max_possible:
                raise ValueError("Max locations per cluster + number of clusters clustering parameters cannot be simultaneously satisfied")
        if max_boxes_per_cluster is not None:
            # Check if it is mathematically possible to meet the constraints on num of clusters + max boxes per cluster
            total_boxes = sum(loc.num_boxes for loc in locations)

            max_possible = num_clusters * max_boxes_per_cluster

            if total_boxes > max_possible:
                raise ValueError("Max boxes per cluster + number of clusters clustering parameters cannot be simultaneously satisfied")
        
        try:
            # Run with timeout
            start_time = time.time()

            # kmeans!
            kmeans = KMeans(
                    n_clusters = num_clusters,
                    random_state = 42,
                    n_init = 10,
            )
            kmeans.fit(coordinates)

            if max_locations_per_cluster is not None or max_boxes_per_cluster is not None:
                # Distrance matrix representing the distance form each point to each centroid
                distances = kmeans.transform(coordinates)
                clusters = self._assign_with_constraints(locations, distances, num_clusters, max_locations_per_cluster, max_boxes_per_cluster)
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
            if timeout_seconds and elapsed > timeout_seconds:
                print(f"Warning: Clustering took {elapsed:.2f}s (exceeded {timeout_seconds}s)")
                return []

            return clusters
        
        except Exception as e:
            print(f"Constrained k-means clustering failed: {e}")
            return []
        
    def _assign_with_constraints(self, locations, distances, num_clusters, max_locations_per_cluster, max_boxes_per_cluster):
        """
        Assign locations to clusters respecting size constraints
        Greedy approach: assign closest points first
        """
         # Assert that only one AT MOST of the limiting max params is set to a value
        assert max_boxes_per_cluster is None or max_locations_per_cluster is None

        # Count number of locations in each cluster
        cluster_counts = defaultdict(int)

        # Hold actual location cluster assignments
        assignments = [None] * len(locations)
        
        # Build candidate list: (location_index, preferred_cluster (by cluster number), distance_to_preferred, all_distances)
        candidates = []
        for i in range(len(locations)):
            best_cluster = int(np.argmin(distances[i]))
            best_distance = distances[i][best_cluster]
            candidates.append((i, best_cluster, best_distance, distances[i]))
        
        # Sort by distance (closest first)
        candidates.sort(key=lambda x: x[2])

        # Helper to check if we can place a location into a cluster w.r.t. constraints + place it if yes
        def can_place_and_put (location_index: int, cluster_id: int) -> bool:
            loc = locations[location_index]

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
        
        # Assign each location "greedily" - assign location to closest cluster with space
        for location_index, preferred_cluster, distance_to_preferred, all_distances in candidates:
            # Try the location's preferred cluster first
            if can_place_and_put(location_index, preferred_cluster):
                continue

            sorted_clusters = np.argsort(all_distances)
            placed = False
            for cluster_id in sorted_clusters:
                cluster_id = int(cluster_id)
                if can_place_and_put(location_index, cluster_id):
                    placed = True
                    break

            if not placed:
                raise ValueError(f"Unable to assign location index {location_index} under constraints")
        
        # Build result lists (each list corresponds to locations in a different cluster)
        clusters = [[] for _ in range(num_clusters)]
        for i, location in enumerate(locations):
            clusters[assignments[i]].append(location)
        
        return clusters
        

        

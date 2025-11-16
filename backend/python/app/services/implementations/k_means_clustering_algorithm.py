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
        if not locations:
            return [[] for _ in range(num_clusters)]
        
        # Extract lat and long coords into a numpy array
        coordinates = np.array([[location.latitude, location.longitude] for location in locations])

        if max_locations_per_cluster:
            # Check if it is mathematically possible to meet the constraints on num of clusters + max locations per cluster
            total_locations = len(locations)
            max_possible = num_clusters * max_locations_per_cluster

            if total_locations > max_possible:
                raise ValueError("Clustering parameters cannot be satisfied")
        
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

            if max_locations_per_cluster:
                # Distrance matrix representing the distance form each point to each centroid
                distances = kmeans.transform(coordinates)
                clusters = self._assign_with_constraints(locations, distances, num_clusters, max_locations_per_cluster)
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
        
    def _assign_with_constraints(self, locations, distances, num_clusters, max_per_cluster):
        """
        Assign locations to clusters respecting size constraints
        Greedy approach: assign closest points first
        """
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
        
        # Assign each location "greedily" - assign location to closest cluster with space
        for location_index, preferred_cluster, distance_to_preferred, all_distances in candidates:
            # Try the location's preferred cluster first
            # Look at each cluster, see if num of locations assigned to that cluster is still within max limit
            # Because using defaultdict, "not-yet-touched" clusters have num locations = 0 by default
            if cluster_counts[preferred_cluster] < max_per_cluster:
                # If still have space in preferred cluster, add location
                assignments[location_index] = preferred_cluster
                cluster_counts[preferred_cluster] += 1
            else:
                # Find nearest cluster with available space
                sorted_clusters = np.argsort(all_distances)
                for cluster_id in sorted_clusters:
                    cluster_id = int(cluster_id)
                    # Check if cluster has space, if not, add the location to the cluster
                    if cluster_counts[cluster_id] < max_per_cluster:
                        assignments[location_index] = cluster_id
                        cluster_counts[cluster_id] += 1
                        break
        
        # Build result lists (each list corresponds to locations in a different cluster)
        clusters = [[] for _ in range(num_clusters)]
        for i, location in enumerate(locations):
            clusters[assignments[i]].append(location)
        
        return clusters
        

        

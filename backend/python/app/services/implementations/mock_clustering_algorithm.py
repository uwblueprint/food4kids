from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.protocols.clustering_algorithm import (
    ClusteringAlgorithmProtocol,
)

if TYPE_CHECKING:
    from app.models.location import Location


class MockClusteringAlgorithm(ClusteringAlgorithmProtocol):
    """Simple mock clustering algorithm that splits locations evenly into clusters.

    This is a pure function with no database interaction - it just
    distributes locations evenly across the requested number of clusters.
    """

    async def cluster_locations(
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
            max_locations_per_cluster: Optional maximum number of locations
                per cluster. If provided, validates that the clustering is
                possible and raises an error if violated.
            timeout_seconds: Optional timeout in seconds. Not enforced in this
                mock implementation.

        Returns:
            List of clusters, where each cluster is a list of locations

        Raises:
            ValueError: If the clustering parameters are invalid or cannot
                be satisfied
        """
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
        if max_locations_per_cluster and max_cluster_size > max_locations_per_cluster:
            raise ValueError(
                f"Cannot create {num_clusters} clusters with max "
                f"{max_locations_per_cluster} locations per cluster. "
                f"Required cluster size would be up to {max_cluster_size}."
            )

        # Distribute remainder locations across the first 'remainder' clusters
        clusters = []
        start = 0
        for i in range(num_clusters):
            size = base_cluster_size + (1 if i < remainder else 0)
            clusters.append(locations[start : start + size])
            start += size
        return clusters

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.protocols.clustering_algorithm import (
    ClusteringAlgorithmProtocol,
)
from app.utilities.boxes import compute_boxes

if TYPE_CHECKING:
    from app.models.location import Location


class MockClusteringAlgorithm(ClusteringAlgorithmProtocol):
    """Simple mock clustering algorithm that splits locations into clusters.

    This is a pure function with no database interaction. It distributes
    locations across clusters while respecting the max_boxes_per_cluster
    constraint.
    """

    def __init__(self, children_per_box: int) -> None:
        self._children_per_box = children_per_box

    async def cluster_locations(
        self,
        locations: list[Location],
        num_clusters: int,
        max_boxes_per_cluster: int | None = None,
        timeout_seconds: float | None = None,  # noqa: ARG002
    ) -> list[list[Location]]:
        """Split locations into clusters while respecting box constraints.

        Args:
            locations: List of locations to cluster
            num_clusters: Target number of clusters to create
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
        if len(locations) == 0:
            raise ValueError("locations list cannot be empty")

        if num_clusters < 1:
            raise ValueError("num_clusters must be at least 1")

        # Calculate base cluster size and validate constraints
        total_locations = len(locations)
        base_cluster_size = total_locations // num_clusters

        if base_cluster_size == 0:
            raise ValueError(
                f"Cannot create {num_clusters} clusters: not enough locations"
            )

        # Distribute locations while respecting constraints
        clusters: list[list[Location]] = [[] for _ in range(num_clusters)]
        cluster_boxes: list[int] = [0] * num_clusters
        cluster_idx = 0

        for location in locations:
            location_boxes = compute_boxes(
                location.num_children, self._children_per_box
            )
            # Find next cluster that can accommodate this location
            attempts = 0
            while attempts < num_clusters:
                boxes_ok = (
                    max_boxes_per_cluster is None
                    or cluster_boxes[cluster_idx] + location_boxes
                    <= max_boxes_per_cluster
                )
                if boxes_ok:
                    break
                cluster_idx = (cluster_idx + 1) % num_clusters
                attempts += 1
            else:
                raise ValueError(
                    "Cannot assign location: no cluster can accommodate it with the given constraints."
                )
            clusters[cluster_idx].append(location)
            cluster_boxes[cluster_idx] += location_boxes
            cluster_idx = (cluster_idx + 1) % num_clusters

        return clusters

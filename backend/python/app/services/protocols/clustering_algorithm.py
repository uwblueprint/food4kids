from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.models.location import Location


class ClusteringAlgorithmProtocol(Protocol):
    """Protocol for clustering algorithms, so implementations can be swapped in.

    Pure functions from locations + parameters to clusters, with no database
    access. Async because an implementation may call out for distances.
    """

    async def cluster_locations(
        self,
        locations: list[Location],
        num_clusters: int,
        max_boxes_per_cluster: int,
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:  # pragma: no cover - interface only
        """Cluster locations into groups.

        Args:
            locations: List of locations to cluster
            num_clusters: Target number of clusters to create
            max_boxes_per_cluster: Maximum number of boxes per cluster, from
                SystemSettings.boxes_per_car. Required: an implementation that
                defaulted it would plan against a capacity nobody configured.
                If it cannot be satisfied with the given number of clusters,
                the algorithm should raise an error.
            timeout_seconds: Optional timeout in seconds. If provided, the
                algorithm should raise TimeoutError if execution exceeds this
                duration. If None, no timeout is enforced.

        Returns:
            List of clusters, where each cluster is a list of locations

        Raises:
            ValueError: If the clustering parameters are invalid or cannot
                be satisfied (e.g., num_clusters < 1, or max_boxes_per_cluster
                is too small for the given number of locations and clusters)
            TimeoutError: If timeout_seconds is provided and execution exceeds
                the timeout duration
        """
        ...

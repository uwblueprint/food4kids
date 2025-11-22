from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.models.location import Location


class ClusteringAlgorithmProtocol(Protocol):
    """Protocol for clustering algorithms.

    Clustering algorithms are pure functions that take a list of locations and
    clustering parameters, and return clusters (each cluster is a list of locations).
    Algorithms should not interact with the database - they only compute
    the cluster assignments.

    Multiple clustering approaches may be used in the final product, so this
    protocol allows for different implementations to be swapped in.

    Algorithms may call external APIs (e.g., for distance calculations) or
    perform long computations, so they are async to allow for efficient
    concurrent operations.
    """

    async def cluster_locations(
        self,
        locations: list[Location],
        num_clusters: int,
        max_locations_per_cluster: int | None = None,
        max_boxes_per_cluster: int | None = None,
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:  # pragma: no cover - interface only
        """Cluster locations into groups.

        Args:
            locations: List of locations to cluster
            num_clusters: Target number of clusters to create
            max_locations_per_cluster: Optional maximum number of locations
                per cluster. If provided and cannot be satisfied with the given
                number of clusters, the algorithm should raise an error. Can
                assert that at most one of the max_locations_per_cluster
                and max_boxes_per_cluster args are non-null (at least for now).
            max_boxes_per_cluster: Optional maximum number of boxes per cluster.
                If provided and cannot be satisfied with the given
                number of clusters, the algorithm should raise an error. Can
                assert that at most one of the max_locations_per_cluster
                and max_boxes_per_cluster args are non-null (at least for now).
            timeout_seconds: Optional timeout in seconds. If provided, the
                algorithm should raise TimeoutError if execution exceeds this
                duration. If None, no timeout is enforced.

        Returns:
            List of clusters, where each cluster is a list of locations

        Raises:
            ValueError: If the clustering parameters are invalid or cannot
                be satisfied (e.g., num_clusters < 1, or max_locations_per_cluster
                is too small for the given number of locations and clusters)
            TimeoutError: If timeout_seconds is provided and execution exceeds
                the timeout duration
        """
        ...

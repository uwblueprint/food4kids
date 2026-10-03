"""Single-vehicle route ordering via the Routes API.

The middle rung of the generation cascade. Our clustering decides which stops
go to which driver; Google then puts each driver's stops in the best order.

That split is what makes this a cheaper tier than Fleet Routing rather than a
worse one at the same price. Fleet Routing bills per *shipment* and does both
jobs — assignment and ordering — in one pass over every stop. computeRoutes
bills per *request*, and we send one request per driver, so a 75-stop run costs
12 units here against roughly 75 there. The quality we give up is assignment:
Fleet Routing weighs every stop against every vehicle at once, while this
inherits whatever clusters the sweep produced.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from google.api_core import exceptions as google_exceptions
from google.api_core.client_options import ClientOptions
from google.maps import routing_v2

from app.config import settings as app_settings
from app.services.implementations.quota_service import PartiallyBilledError
from app.services.implementations.sweep_clustering import (
    DEFAULT_MAX_BOXES_PER_CLUSTER,
    SweepClusteringAlgorithm,
)

if TYPE_CHECKING:
    from app.models.location import Location
    from app.schemas.route_generation import RouteGenerationSettings
    from app.services.protocols.clustering_algorithm import ClusteringAlgorithmProtocol

logger = logging.getLogger(__name__)

# Only the optimised ordering is needed here; polylines and distances are
# fetched separately when the generation is saved. Asking for less keeps the
# response small and the field mask honest about what we use.
FIELD_MASK = "routes.optimizedIntermediateWaypointIndex"

# A single computeRoutes request accepts at most this many intermediates.
# Clusters are far smaller in practice (~6 stops), but a mis-set route count
# could produce one oversized cluster, and a silent truncation would drop
# deliveries.
MAX_INTERMEDIATES = 25


class RoutesApiRoutingError(Exception):
    """Raised when the Routes API cannot order a cluster."""


class RoutesApiRequestNotSentError(RoutesApiRoutingError):
    """Raised when a cluster's request failed before it was sent.

    Distinguished because nothing was billed: the cascade may hand those
    units back, where a request Google answered with an error it may not.
    """


def _remaining(timeout_seconds: float | None, started: float) -> float | None:
    """What is left of the tier's budget, or None when it is unbounded.

    Clamped at zero rather than going negative, so a budget already spent by
    clustering times out immediately instead of being read as "no timeout".
    """
    if timeout_seconds is None:
        return None
    return max(timeout_seconds - (time.monotonic() - started), 0.0)


class RoutesApiSingleVehicleAlgorithm:
    """Clusters in-house, then orders each cluster with the Routes API."""

    clustering_algorithm: ClusteringAlgorithmProtocol

    def __init__(
        self, warehouse_lat: float, warehouse_lon: float, children_per_box: int
    ) -> None:
        self.warehouse_lat = warehouse_lat
        self.warehouse_lon = warehouse_lon
        self.clustering_algorithm = SweepClusteringAlgorithm(
            warehouse_lat=warehouse_lat,
            warehouse_lon=warehouse_lon,
            children_per_box=children_per_box,
        )

    async def generate_routes(
        self,
        locations: list[Location],
        warehouse_lat: float,
        warehouse_lon: float,
        settings: RouteGenerationSettings,
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:
        """Cluster the stops, then order each cluster via the Routes API."""
        if not locations:
            return []

        started = time.monotonic()
        clusters = await self.clustering_algorithm.cluster_locations(
            locations=locations,
            num_clusters=settings.num_routes,
            max_boxes_per_cluster=DEFAULT_MAX_BOXES_PER_CLUSTER,
            timeout_seconds=timeout_seconds,
        )

        # One request per non-empty cluster, issued together: they are
        # independent, and serialising them would multiply the wall-clock cost
        # of a tier that is meant to be the cheap one.
        #
        # Bounded by whatever is left of this tier's budget after clustering.
        # Without it a hanging Google response would only stop at the job-level
        # timeout, which fails the whole job — the cascade needs a TimeoutError
        # from *this* tier to fall back to the free cluster+sweep instead.
        #
        # return_exceptions so one failed cluster does not hide how many of
        # its siblings were already answered, and billed, by Google.
        results = await asyncio.wait_for(
            asyncio.gather(
                *(
                    self._order_cluster(
                        cluster,
                        warehouse_lat,
                        warehouse_lon,
                        settings.return_to_warehouse,
                    )
                    for cluster in clusters
                ),
                return_exceptions=True,
            ),
            timeout=_remaining(timeout_seconds, started),
        )

        ordered: list[list[Location]] = []
        failures: list[Exception] = []
        for result in results:
            if isinstance(result, Exception):
                failures.append(result)
            elif isinstance(result, BaseException):
                raise result
            else:
                ordered.append(result)

        if failures:
            # Every cluster that needed ordering issued a request, and only the
            # ones that failed before sending went unbilled. A request Google
            # answered with an error counts as billed: overcounting costs a
            # worse route, undercounting costs money.
            issued = sum(1 for cluster in clusters if len(cluster) >= 2)
            unsent = sum(
                1 for f in failures if isinstance(f, RoutesApiRequestNotSentError)
            )
            raise PartiallyBilledError(
                f"{len(failures)} of {len(clusters)} cluster(s) could not be "
                "ordered by the Routes API.",
                units_billed=issued - unsent,
            ) from failures[0]

        return ordered

    async def _order_cluster(
        self,
        cluster: list[Location],
        warehouse_lat: float,
        warehouse_lon: float,
        return_to_warehouse: bool,
    ) -> list[Location]:
        """Return one cluster's stops in the order Google recommends.

        Ordering fewer than two stops is a no-op, so those clusters skip the
        call entirely rather than spending a request to learn nothing.
        """
        if len(cluster) < 2:
            return list(cluster)

        if len(cluster) > MAX_INTERMEDIATES:
            raise RoutesApiRequestNotSentError(
                f"Cluster of {len(cluster)} stops exceeds the Routes API's "
                f"{MAX_INTERMEDIATES}-waypoint limit."
            )

        order = await self._request_order(
            cluster, warehouse_lat, warehouse_lon, return_to_warehouse
        )
        return [cluster[i] for i in order]

    async def _request_order(
        self,
        cluster: list[Location],
        warehouse_lat: float,
        warehouse_lon: float,
        return_to_warehouse: bool,
    ) -> list[int]:
        """Ask the Routes API for the best visit order, as cluster indices."""
        if not app_settings.google_maps_api_key:
            raise RoutesApiRequestNotSentError(
                "Routes API ordering is not configured. Set GOOGLE_MAPS_API_KEY."
            )

        warehouse = routing_v2.Waypoint(
            location=routing_v2.Location(
                lat_lng={"latitude": warehouse_lat, "longitude": warehouse_lon}
            )
        )
        stops = [
            routing_v2.Waypoint(
                location=routing_v2.Location(
                    lat_lng={"latitude": loc.latitude, "longitude": loc.longitude}
                )
            )
            for loc in cluster
        ]

        # When drivers do not return to the depot the last stop is the
        # destination, so it is fixed and only the rest get reordered. Its
        # index is appended back on below.
        if return_to_warehouse:
            destination, intermediates = warehouse, stops
            trailing: list[int] = []
        else:
            destination, intermediates = stops[-1], stops[:-1]
            trailing = [len(cluster) - 1]

        request = routing_v2.ComputeRoutesRequest(
            origin=warehouse,
            destination=destination,
            intermediates=intermediates,
            travel_mode=routing_v2.RouteTravelMode.DRIVE,
            routing_preference=routing_v2.RoutingPreference.TRAFFIC_AWARE,
            optimize_waypoint_order=True,
        )

        try:
            client = routing_v2.RoutesAsyncClient(
                client_options=ClientOptions(api_key=app_settings.google_maps_api_key)
            )
            response = await client.compute_routes(
                request=request, metadata=[("x-goog-fieldmask", FIELD_MASK)]
            )
        except google_exceptions.PermissionDenied as e:
            raise RoutesApiRoutingError(
                "Routes API ordering failed: permission denied."
            ) from e
        except google_exceptions.GoogleAPICallError as e:
            raise RoutesApiRoutingError(
                "Routes API ordering failed: upstream error."
            ) from e

        if not response.routes:
            raise RoutesApiRoutingError("Routes API returned no route for a cluster.")

        order = list(response.routes[0].optimized_intermediate_waypoint_index)

        # A response that does not reorder (or omits the field) must not be
        # allowed to drop or duplicate stops — silently losing a delivery is
        # far worse than a slightly longer drive.
        if sorted(order) != list(range(len(intermediates))):
            logger.warning(
                "Routes API returned an unusable waypoint order (%d of %d "
                "indices); keeping the cluster's original order",
                len(order),
                len(intermediates),
            )
            return list(range(len(cluster)))

        return order + trailing

from __future__ import annotations

import asyncio
import logging
import threading
from typing import TYPE_CHECKING

import google.auth.transport.requests
import requests
from google.oauth2 import service_account

from app.config import settings as app_settings
from app.services.protocols.routing_algorithm import RoutingAlgorithmProtocol

if TYPE_CHECKING:
    from app.models.location import Location
    from app.schemas.route_generation import RouteGenerationSettings

logger = logging.getLogger(__name__)

ENDPOINT = "https://routeoptimization.googleapis.com/v1/projects/{}:optimizeTours"
SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
API_TIMEOUT_SECONDS = 60

# Penalty cost high enough that the optimizer will never skip a delivery.
MANDATORY_DELIVERY_PENALTY = 1_000_000

# Cost per hour the optimizer charges when a route exceeds its soft duration
# limit. Higher values spread deliveries more aggressively across drivers.
DURATION_OVERRUN_COST_PER_HOUR = 100


class GoogleMapsFleetRoutingAlgorithm(RoutingAlgorithmProtocol):
    """Routes locations using the Google Cloud Fleet Routing (optimizeTours) API."""

    def __init__(self) -> None:
        self._credentials: service_account.Credentials | None = None
        self._credentials_lock = threading.Lock()

    async def generate_routes(
        self,
        locations: list[Location],
        warehouse_lat: float,
        warehouse_lon: float,
        settings: RouteGenerationSettings,
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:
        """Call the Fleet Routing API and parse the response into routes."""

        if not locations:
            return []

        payload = self._build_payload(locations, warehouse_lat, warehouse_lon, settings)

        response_json = await asyncio.wait_for(
            asyncio.to_thread(self._call_api, payload),
            timeout=timeout_seconds,
        )

        return self._parse_response(response_json, locations, settings.num_routes)

    def _build_payload(
        self,
        locations: list[Location],
        warehouse_lat: float,
        warehouse_lon: float,
        settings: RouteGenerationSettings,
    ) -> dict:
        """Build the optimizeTours request payload using v1 API field names."""

        warehouse = {"latitude": warehouse_lat, "longitude": warehouse_lon}
        max_stops = settings.max_stops_per_route

        load_limit = (
            {"loadLimits": {"load": {"maxLoad": str(max_stops)}}}
            if max_stops is not None
            else {}
        )

        # routeDurationLimit: soft cap on total route time. The optimizer
        # penalises routes that exceed this, spreading deliveries more evenly
        # across drivers without hard-blocking longer routes.
        duration_limit = (
            {
                "routeDurationLimit": {
                    "softMaxDuration": f"{settings.route_duration_limit_minutes * 60}s",
                    "costPerHourAfterSoftMax": DURATION_OVERRUN_COST_PER_HOUR,
                }
            }
            if settings.route_duration_limit_minutes is not None
            else {}
        )

        # endLocation controls whether drivers return to the warehouse.
        # During school term drivers return; during summer they end at their
        # last delivery to save time.
        vehicles = [
            {
                "displayName": f"driver_{i}",
                "startLocation": warehouse,
                **({"endLocation": warehouse} if settings.return_to_warehouse else {}),
                **load_limit,
                **duration_limit,
            }
            for i in range(settings.num_routes)
        ]

        # Force every vehicle to be used by giving each a mandatory pickup.
        # Without this some drivers may be left idle.
        # loadDemands is explicitly 0 so it doesn't consume capacity meant
        # for actual deliveries (each delivery adds 1 to the load).
        forced_pickups = [
            {
                "displayName": f"initial_load_driver_{i}",
                "pickups": [
                    {
                        "arrivalLocation": warehouse,
                        "loadDemands": {"load": {"amount": "0"}},
                    }
                ],
                "allowedVehicleIndices": [i],
            }
            for i in range(settings.num_routes)
        ]

        service_duration = f"{settings.service_time_minutes * 60}s"

        deliveries = [
            {
                "displayName": f"ship_{i}",
                # High penalty ensures the API never skips a delivery —
                # every location must be served.
                "penaltyCost": MANDATORY_DELIVERY_PENALTY,
                "deliveries": [
                    {
                        "arrivalLocation": {
                            "latitude": loc.latitude,
                            "longitude": loc.longitude,
                        },
                        "duration": service_duration,
                        "loadDemands": {"load": {"amount": "1"}},
                    }
                ],
            }
            for i, loc in enumerate(locations)
        ]

        # TODO: use settings.route_start_time to set
        # globalStartTime / globalEndTime or per-shipment timeWindows

        return {
            "model": {"vehicles": vehicles, "shipments": forced_pickups + deliveries}
        }

    def _ensure_credentials(self) -> service_account.Credentials:
        """Return cached credentials, refreshing only when expired.

        Thread-safe: _call_api runs in asyncio.to_thread, so concurrent
        requests could race here without the lock.
        """
        with self._credentials_lock:
            if self._credentials is None or not self._credentials.valid:
                if not app_settings.route_opt_client_email:
                    raise RuntimeError(
                        "Fleet Routing service account credentials are not configured. "
                        "Set the ROUTE_OPT_* environment variables."
                    )
                info = {
                    "type": "service_account",
                    "project_id": app_settings.route_opt_project_id,
                    "private_key_id": app_settings.route_opt_private_key_id,
                    "private_key": app_settings.route_opt_private_key.replace(
                        "\\n", "\n"
                    ),
                    "client_email": app_settings.route_opt_client_email,
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
                self._credentials = (
                    service_account.Credentials.from_service_account_info(
                        info, scopes=SCOPES
                    )
                )
                self._credentials.refresh(google.auth.transport.requests.Request())
            return self._credentials

    def _call_api(self, payload: dict) -> dict:
        """Make the HTTP request to the Fleet Routing API (runs in a thread)."""

        credentials = self._ensure_credentials()

        url = ENDPOINT.format(app_settings.route_opt_project_id)
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {credentials.token}"},
            json=payload,
            timeout=API_TIMEOUT_SECONDS,
        )
        if not response.ok:
            logger.error(
                "Fleet Routing API error %s: %s", response.status_code, response.text
            )
        response.raise_for_status()
        result: dict = response.json()
        return result

    def _parse_response(
        self,
        result: dict,
        locations: list[Location],
        num_routes: int,
    ) -> list[list[Location]]:
        """Parse the optimizeTours response into grouped, ordered routes.

        The API response contains a list of routes (one per vehicle) with visits.
        Each visit references a shipment index. We skip the forced-pickup shipments
        (indices 0..num_routes-1) and map the remaining delivery shipments back to
        locations using: location_index = shipment_index - num_routes.
        """

        # Every delivery is mandatory — if the API skipped any, something is
        # misconfigured (e.g. not enough vehicles or capacity).
        skipped = result.get("skippedShipments", [])
        if skipped:
            skipped_names = [s.get("label", s.get("index", "?")) for s in skipped]
            raise RuntimeError(
                f"Fleet Routing API skipped {len(skipped)} shipments: {skipped_names}. "
                "All deliveries must be served — check vehicle count and capacity."
            )

        routes: list[list[Location]] = [[] for _ in range(num_routes)]

        for route_data in result.get("routes", []):
            vehicle_index = route_data.get("vehicleIndex", 0)
            if vehicle_index >= num_routes:
                logger.warning(
                    "Unexpected vehicleIndex %d (expected < %d), skipping route",
                    vehicle_index,
                    num_routes,
                )
                continue

            for visit in route_data.get("visits", []):
                if visit.get("isPickup", False):
                    continue
                shipment_index = visit.get("shipmentIndex", 0)
                # Offset by num_routes because forced-pickup shipments occupy
                # indices 0..num_routes-1 in the shipments array.
                location_index = shipment_index - num_routes
                # Guard also protects against missing shipmentIndex
                # (defaults to 0, yielding a negative location_index)
                if 0 <= location_index < len(locations):
                    routes[vehicle_index].append(locations[location_index])

        return routes

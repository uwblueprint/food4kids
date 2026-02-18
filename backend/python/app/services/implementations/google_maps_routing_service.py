from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

import google.auth.transport.requests
import requests
from google.oauth2 import service_account

from app.config import settings
from app.services.protocols.routing_algorithm import RoutingAlgorithmProtocol

if TYPE_CHECKING:
    from app.models.location import Location
    from app.schemas.route_generation import RouteGenerationSettings

logger = logging.getLogger(__name__)

ENDPOINT = "https://routeoptimization.googleapis.com/v1/projects/{}:optimizeTours"
SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
API_TIMEOUT_SECONDS = 60


class GoogleMapsFleetRoutingAlgorithm(RoutingAlgorithmProtocol):
    """Routes locations using the Google Cloud Fleet Routing (optimizeTours) API."""

    def __init__(self) -> None:
        self._credentials: service_account.Credentials | None = None

    async def generate_routes(
        self,
        locations: list[Location],
        warehouse_lat: float,
        warehouse_lon: float,
        route_settings: RouteGenerationSettings,
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:
        """Call the Fleet Routing API and parse the response into routes."""

        if not locations:
            return []

        payload = self._build_payload(
            locations, warehouse_lat, warehouse_lon, route_settings
        )

        response_json = await asyncio.wait_for(
            asyncio.to_thread(self._call_api, payload),
            timeout=timeout_seconds,
        )

        return self._parse_response(response_json, locations, route_settings.num_routes)

    def _build_payload(
        self,
        locations: list[Location],
        warehouse_lat: float,
        warehouse_lon: float,
        route_settings: RouteGenerationSettings,
    ) -> dict:
        """Build the optimizeTours request payload using v1 API field names."""

        warehouse = {"latitude": warehouse_lat, "longitude": warehouse_lon}
        max_stops = route_settings.max_stops_per_route

        load_limit = (
            {"loadLimits": {"load": {"maxLoad": str(max_stops)}}}
            if max_stops is not None
            else {}
        )

        vehicles = [
            {
                "displayName": f"driver_{i}",
                "startLocation": warehouse,
                **(
                    {"endLocation": warehouse}
                    if route_settings.return_to_warehouse
                    else {}
                ),
                **load_limit,
            }
            for i in range(route_settings.num_routes)
        ]

        # Force every vehicle to be used by giving each a mandatory pickup.
        # Without this some drivers may be left idle.
        # Load demand is set to 0 so it doesn't consume capacity meant for
        # actual deliveries (each delivery adds 1 to the load).
        forced_pickups = [
            {
                "displayName": f"initial_load_driver_{i}",
                "pickups": [
                    {
                        "arrivalLocation": warehouse,
                    }
                ],
                "allowedVehicleIndices": [i],
            }
            for i in range(route_settings.num_routes)
        ]

        deliveries = [
            {
                "displayName": f"ship_{i}",
                "deliveries": [
                    {
                        "arrivalLocation": {
                            "latitude": loc.latitude,
                            "longitude": loc.longitude,
                        },
                        "loadDemands": {"load": {"amount": "1"}},
                    }
                ],
            }
            for i, loc in enumerate(locations)
        ]

        # TODO: use route_settings.route_start_time to set
        # globalStartTime / globalEndTime or per-shipment timeWindows

        return {"model": {"vehicles": vehicles, "shipments": forced_pickups + deliveries}}

    def _ensure_credentials(self) -> service_account.Credentials:
        """Return cached credentials, refreshing only when expired."""
        if self._credentials is None or not self._credentials.valid:
            if not settings.route_opt_client_email:
                raise RuntimeError(
                    "Fleet Routing service account credentials are not configured. "
                    "Set the ROUTE_OPT_* environment variables."
                )
            info = {
                "type": "service_account",
                "project_id": settings.route_opt_project_id,
                "private_key_id": settings.route_opt_private_key_id,
                "private_key": settings.route_opt_private_key.replace("\\n", "\n"),
                "client_email": settings.route_opt_client_email,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            self._credentials = service_account.Credentials.from_service_account_info(
                info, scopes=SCOPES
            )
            self._credentials.refresh(google.auth.transport.requests.Request())
        return self._credentials

    def _call_api(self, payload: dict) -> dict:
        """Make the HTTP request to the Fleet Routing API (runs in a thread)."""

        credentials = self._ensure_credentials()

        url = ENDPOINT.format(settings.route_opt_project_id)
        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {credentials.token}",
            },
            data=json.dumps(payload),
            timeout=API_TIMEOUT_SECONDS,
        )
        if not response.ok:
            logger.error("Fleet Routing API error %s: %s", response.status_code, response.text)
        response.raise_for_status()
        return response.json()

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
                location_index = shipment_index - num_routes
                # Guard also protects against missing shipmentIndex
                # (defaults to 0, yielding a negative location_index)
                if 0 <= location_index < len(locations):
                    routes[vehicle_index].append(locations[location_index])

        return routes

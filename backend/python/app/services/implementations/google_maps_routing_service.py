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


class GoogleMapsFleetRoutingAlgorithm(RoutingAlgorithmProtocol):
    """Routes locations using the Google Cloud Fleet Routing (optimizeTours) API."""

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

        vehicles = [
            {
                "displayName": f"driver_{i}",
                "startLocation": warehouse,
                **(
                    {"loadLimits": {"load": {"maxLoad": str(route_settings.max_stops_per_route)}}}
                    if route_settings.max_stops_per_route is not None
                    else {}
                ),
            }
            for i in range(route_settings.num_routes)
        ]

        # Force every vehicle to be used by giving each a mandatory pickup, without this some drivers may be left idle
        forced_pickups = [
            {
                "displayName": f"initial_load_driver_{i}",
                "pickups": [
                    {
                        "arrivalLocation": warehouse,
                        **(
                            {"loadDemands": {"load": {"amount": str(route_settings.max_stops_per_route)}}}
                            if route_settings.max_stops_per_route is not None
                            else {}
                        ),
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

        return {"model": {"vehicles": vehicles, "shipments": forced_pickups + deliveries}}

    def _get_credentials(self) -> service_account.Credentials:
        """Build service account credentials from env vars (same pattern as Firebase)."""
        info = {
            "type": "service_account",
            "project_id": settings.route_opt_project_id,
            "private_key_id": settings.route_opt_private_key_id,
            "private_key": settings.route_opt_private_key.replace("\\n", "\n"),
            "client_email": settings.route_opt_client_email,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        return service_account.Credentials.from_service_account_info(
            info, scopes=SCOPES
        )

    def _call_api(self, payload: dict) -> dict:
        """Make the HTTP request to the Fleet Routing API (runs in a thread)."""

        credentials = self._get_credentials()
        credentials.refresh(google.auth.transport.requests.Request())

        url = ENDPOINT.format(settings.route_opt_project_id)
        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {credentials.token}",
            },
            data=json.dumps(payload),
            timeout=60,
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
                continue

            for visit in route_data.get("visits", []):
                if visit.get("isPickup", False):
                    continue
                shipment_index = visit.get("shipmentIndex", 0)
                location_index = shipment_index - num_routes
                if 0 <= location_index < len(locations):
                    routes[vehicle_index].append(locations[location_index])

        return routes

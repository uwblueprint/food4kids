from __future__ import annotations

import requests
import json
import asyncio
from sqlmodel import select
import os

from sqlalchemy.orm import Session
import app.models as db

from typing import TYPE_CHECKING

from app.services.implementations.mock_clustering_algorithm import (
    MockClusteringAlgorithm,
)
from app.services.protocols.routing_algorithm import (
    RoutingAlgorithmProtocol,
)

from app.models.location import Location

if TYPE_CHECKING:
    from app.models.location import Location
    from app.schemas.route_generation import RouteGenerationSettings


API_KEY = os.getenv("ROUTE_OPTIMIZATION_KEY")  # <-- REQUIRED: Replace with your API Key
PROJECT_ID = os.getenv("PROJECT_ID")  # <-- REQUIRED: Replace with your GCP Project ID

ENDPOINT = f"https://routeoptimization.googleapis.com/v1/projects/{PROJECT_ID}/optimizeTours"


class GoogleMapsFleetRoutingAlgorithm(RoutingAlgorithmProtocol):
    """Simple mock routing algorithm that uses the mock clustering algorithm."""

    def generate_routes(
        self,
        locations: list[Location],
        warehouse_lat: float,
        warehouse_lng: float,
        settings: RouteGenerationSettings,
    ) -> list[list[Location]]:
        """Split locations evenly across routes using the mock clustering algorithm."""

        vehicles = [
            {
                "vehicleId": f"driver_{i}",
                "startLocation": {"latLng": {"latitude": warehouse_lat, "longitude": warehouse_lng}},
                "capacityLimits": {"load": settings.max_stops_per_route}
            }
            for i in range(settings.num_routes)
        ]

        # Force Google Maps to use ALL drivers, it might try skimping out
        forced_pickups = []
        for i in range(settings.num_routes):
            driver_id = f"driver_{i}"
            forced_pickups.append({
                "shipmentId": f"initial_load_{driver_id}",
                # Use a pickup to represent the vehicle being loaded at the start.
                "pickups": [
                    {
                        "visitRequestId": f"initial_pick_{driver_id}",
                        "location": {"latLng": {"latitude": warehouse_lat, "longitude": warehouse_lng}},
                        "loadDemands": {"load": settings.max_stops_per_route} 
                    }
                ],
                # CRITICAL CONSTRAINT: Only this specific vehicle can service this initial load.
                "usedVehicleConstraint": {
                    "requiredVehicles": [driver_id]
                }
            })

        # --- 3. Define Standard Deliveries ---
        standard_deliveries = [
            {
                "shipmentId": f"ship_{i}",
                "deliveries": [
                    {
                        "visitRequestId": f"loc_{i}",
                        "location": {"latLng": {"latitude": loc.latitude, "longitude": loc.longitude}},
                        "loadDemands": {"load": 1} 
                    }
                ]
            }
            for i, loc in enumerate(locations)
        ]

        # --- 4. Combine Shipments ---
        # The final shipments array is the combination of the forced pickups and the standard deliveries.
        shipments = forced_pickups + standard_deliveries

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY # Use the key defined in the class
        }

        payload = {
            "model":{
                "vehicles": vehicles,
                "shipments": shipments
            }
        }

        try:
            response = requests.post(
                ENDPOINT, 
                headers=headers, 
                data=json.dumps(payload),
                timeout=45 # Set a timeout slightly longer than the global duration limit
            )
            
            # This will raise an HTTPError for bad responses (4xx or 5xx status codes)
            response.raise_for_status() 
            result = response.json()
            
            print (result)
            return [] # Placeholder return

        except requests.exceptions.HTTPError as errh:
            print(f"Http Error: {errh}")
            # Raise exception or handle error gracefully
            raise
        except requests.exceptions.ConnectionError as errc:
            print(f"Error Connecting: {errc}")
            raise
        except requests.exceptions.Timeout as errt:
            print(f"Timeout Error: {errt}")
            raise
        except requests.exceptions.RequestException as err:
            print(f"An unknown error occurred: {err}")
            raise


test = GoogleMapsFleetRoutingAlgorithm()

async def print_all_locations():
    # Initialize database
    db.init_app()


    async with db.async_session_maker_instance() as session:
        # Use SQLAlchemy select()
        result = await session.execute(select(Location))
        locations = result.scalars().all()

        for loc in locations:
            print(f"ID: {loc.id}, Name: {loc.name}, Lat: {loc.latitude}, Lng: {loc.longitude}")

    return locations


if __name__ == "__main__":
    asyncio.run(print_all_locations())

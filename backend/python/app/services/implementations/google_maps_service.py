from __future__ import annotations

import asyncio
import json
import os
from typing import TYPE_CHECKING

import requests
from sqlmodel import select

import app.models as db
from app.models.location import Location
from app.services.implementations.mock_clustering_algorithm import (
    MockClusteringAlgorithm,
)
from app.services.protocols.routing_algorithm import (
    RoutingAlgorithmProtocol,
)

if TYPE_CHECKING:
    from app.schemas.route_generation import RouteGenerationSettings


API_KEY = os.getenv("ROUTE_OPTIMIZATION_KEY")  # <-- REQUIRED: Replace with your API Key

ENDPOINT = "https://routes.googleapis.com/directions/v2:computeRoutes"




class GoogleMapsFleetRoutingAlgorithm(RoutingAlgorithmProtocol):
    """Routing algorithm that uses Google Maps Routes API v2 with clustering."""

    async def generate_routes(
        self,
        locations: list[Location],
        warehouse_lat: float,
        warehouse_lon: float,
        settings: RouteGenerationSettings,
        timeout_seconds: float | None = None,
    ) -> list[list[Location]]:
        """Generate routes from a list of locations using Google Maps Routes API v2."""
        if len(locations) == 0:
            raise ValueError("locations list cannot be empty")

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": "routes.optimizedIntermediateWaypointIndex,routes.distanceMeters,routes.duration"
        }

        routes = []

        # Cluster locations into groups (one for each vehicle)
        for vehicle_index, clustered_locations in enumerate(
            await MockClusteringAlgorithm().cluster_locations(
                locations, settings.num_routes
            )
        ):
            # Build intermediates from clustered locations
            intermediates = [
                {
                    "location": {
                        "latLng": {
                            "latitude": loc.latitude,
                            "longitude": loc.longitude
                        }
                    }
                }
                for loc in clustered_locations
            ]

            request_body = {
                "origin": {
                    "location": {
                        "latLng": {
                            "latitude": warehouse_lat,
                            "longitude": warehouse_lon
                        }
                    }
                },
                "destination": {
                    "location": {
                        "latLng": {
                            "latitude": warehouse_lat,
                            "longitude": warehouse_lon
                        }
                    }
                },
                "intermediates": intermediates,
                "travelMode": "DRIVE",
                "optimizeWaypointOrder": True
            }

            try:
                response = requests.post(
                    ENDPOINT,
                    headers=headers,
                    data=json.dumps(request_body),
                    timeout=timeout_seconds
                )

                response.raise_for_status()
                response_data = response.json()

                print(f"Route {vehicle_index + 1} response:")
                print(response_data)

                # Extract optimized waypoint order
                if "routes" in response_data and len(response_data["routes"]) > 0:
                    route = response_data["routes"][0]
                    if "optimizedIntermediateWaypointIndex" in route:
                        optimized_indices = route["optimizedIntermediateWaypointIndex"]
                        # Reorder locations based on optimized indices
                        optimized_route = [clustered_locations[i] for i in optimized_indices]
                        routes.append(optimized_route)
                    else:
                        # No optimization performed, use original order
                        routes.append(clustered_locations)
                else:
                    print(f"Warning: No routes returned for vehicle {vehicle_index}")

            except requests.exceptions.HTTPError as errh:
                print(f"Http Error: {errh}")
                print(f"Response: {errh.response.text if errh.response else 'No response'}")
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

        return routes
        



async def test_google_maps_routing():
    """Test Google Maps Routes API v2 with real database locations"""
    # Initialize database
    db.init_app()

    async with db.async_session_maker_instance() as session:
        # Get locations from database
        result = await session.execute(select(Location).limit(10))
        locations = list(result.scalars().all())

        print(f"\n=== Loaded {len(locations)} locations from database ===")
        for loc in locations:
            print(f"  - {loc.contact_name} at ({loc.latitude}, {loc.longitude})")

        if not locations:
            print("No locations found in database. Please seed the database first.")
            return

        # Create test settings
        from datetime import datetime

        from app.schemas.route_generation import RouteGenerationSettings

        settings = RouteGenerationSettings(
            return_to_warehouse=True,
            route_start_time=datetime.now(),
            num_routes=3,
            max_stops_per_route=5
        )

        # Test routing algorithm
        print("\n=== Testing Google Maps Routes API v2 ===")
        print("Warehouse: (43.6532, -79.3832)")
        print(f"Routes: {settings.num_routes}")
        print(f"Max stops per route: {settings.max_stops_per_route}")

        algo = GoogleMapsFleetRoutingAlgorithm()

        try:
            routes = await algo.generate_routes(
                locations=locations,
                warehouse_lat=43.6532,
                warehouse_lon=-79.3832,
                settings=settings,
                timeout_seconds=45
            )

            print(f"\n=== Generated {len(routes)} routes ===")
            for i, route in enumerate(routes):
                print(f"Route {i+1}: {len(route)} stops")
                for loc in route:
                    print(f"  - {loc.contact_name}")

        except Exception as e:
            print("\n=== Error during routing ===")
            print(f"Error: {e}")
            raise


if __name__ == "__main__":
    # Check for required environment variables
    if not API_KEY:
        print("ERROR: Missing required environment variables!")
        print(f"  ROUTE_OPTIMIZATION_KEY: {'✓ Set' if API_KEY else '✗ Not set'}")
        print("\nPlease set this environment variable in your .env file or Docker environment.")
        exit(1)

    print("Starting Google Maps Routes API test...")
    asyncio.run(test_google_maps_routing())

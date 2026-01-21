from typing import TYPE_CHECKING

import googlemaps
from fastapi import HTTPException

if TYPE_CHECKING:
    from app.models.location import Location

async def fetch_route_polyline(
        locations: list["Location"],
        warehouse_lat: float,
        warehouse_lon: float,
        ends_at_warehouse: bool,
        google_maps_client: googlemaps.Client,
) -> tuple[str, float]:
    """Fetch encoded polyline from Google Maps Directions API.
    
    Args:
        locations: Ordered list of Location objects (route stops)
        warehouse_lat: Warehouse latitude
        warehouse_lon: Warehouse longitude
        ends_at_warehouse: If True, route returns to warehouse
        google_maps_client: The googlemaps.Client instance
        
    Returns:
        Tuple with encoded polyline string and total distance in kilometers
        
    Raises:
        HTTPException: If API request fails
        ValueError: If locations list is empty
    """
    if not locations:
        raise ValueError("Locations list cannot be empty")
    
    origin = (warehouse_lat, warehouse_lon)
    waypoints = [(loc.latitude, loc.longitude) for loc in locations]

    if ends_at_warehouse:
        destination = origin
        waypoints_to_use = waypoints
    else:
        if len(waypoints) > 1:
            waypoints_to_use = waypoints[:-1]
            destination = waypoints[-1]
        else:
            waypoints_to_use = []
            destination = waypoints[0]
    
    try:
        directions_result = google_maps_client.directions(
            origin=origin,
            destination=destination,
            waypoints=waypoints_to_use if waypoints_to_use else None,
            mode="driving",
            optimize_waypoints=False, # we can play around with this later
            alternatives=False,
        )

        if not directions_result or len(directions_result) == 0:
            raise HTTPException(
                status_code=500,
                detail="Google Maps API returned no routes",
            )
        
        route = directions_result[0]
        polyline = route["overview_polyline"]["points"]
        total_distance = sum(leg["distance"]["value"] for leg in route["legs"])
        distance_km = total_distance / 1000.0  # convert to kilometers

        return polyline, distance_km
    
    except googlemaps.exceptions.ApiError as e:
        raise HTTPException(
            status_code=503,
            detail="Google Maps API error " + str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Unexpected error when calling Google Maps API: " + str(e),
        ) from e
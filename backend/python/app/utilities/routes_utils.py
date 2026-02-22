from typing import TYPE_CHECKING

from fastapi import HTTPException
from google.api_core import exceptions as google_exceptions
from google.api_core.client_options import ClientOptions
from google.maps import routing_v2

from app.config import settings

if TYPE_CHECKING:
    from app.models.location import Location


async def fetch_route_polyline(
    locations: list["Location"],
    warehouse_lat: float,
    warehouse_lon: float,
    ends_at_warehouse: bool,
) -> tuple[str, float]:
    """Fetch encoded polyline from Google Maps Routes API.

    Args:
        locations: Ordered list of Location objects (route stops)
        warehouse_lat: Warehouse latitude
        warehouse_lon: Warehouse longitude
        ends_at_warehouse: If True, route returns to warehouse

    Returns:
        Tuple with encoded polyline string and total distance in kilometers

    Raises:
        HTTPException: If API request fails
        ValueError: If locations list is empty or API key not configured
    """
    if not locations:
        raise ValueError("Locations list cannot be empty")

    if not settings.google_maps_api_key:
        raise ValueError("Google Maps API key is not configured in settings")

    # Build waypoints
    origin = routing_v2.Waypoint(
        location=routing_v2.Location(
            lat_lng={"latitude": warehouse_lat, "longitude": warehouse_lon}
        )
    )

    intermediates = [
        routing_v2.Waypoint(
            location=routing_v2.Location(
                lat_lng={"latitude": loc.latitude, "longitude": loc.longitude}
            )
        )
        for loc in locations
    ]

    if ends_at_warehouse:
        destination = origin
        waypoints_to_use = intermediates
    else:
        if len(intermediates) > 1:
            waypoints_to_use = intermediates[:-1]
            destination = intermediates[-1]
        else:
            waypoints_to_use = None
            destination = intermediates[0]

    # Build request
    request = routing_v2.ComputeRoutesRequest(
        origin=origin,
        destination=destination,
        intermediates=waypoints_to_use,
        travel_mode=routing_v2.RouteTravelMode.DRIVE,
        routing_preference=routing_v2.RoutingPreference.TRAFFIC_AWARE,
    )

    try:
        # Create client with API key
        options = ClientOptions(api_key=settings.google_maps_api_key)
        client = routing_v2.RoutesAsyncClient(client_options=options)

        response = await client.compute_routes(
            request=request,
            metadata=[
                (
                    "x-goog-fieldmask",
                    "routes.polyline.encodedPolyline,routes.distanceMeters",
                )
            ],
        )

        if not response.routes:
            raise HTTPException(
                status_code=500,
                detail="Google Maps API returned no routes",
            )

        route = response.routes[0]
        polyline = route.polyline.encoded_polyline
        distance_km = route.distance_meters / 1000.0

        return polyline, distance_km

    except google_exceptions.GoogleAPICallError as e:
        raise HTTPException(
            status_code=503, detail=f"Google Maps API error: {e!s}"
        ) from e
    except google_exceptions.RetryError as e:
        raise HTTPException(status_code=504, detail="Request timed out") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e!s}") from e

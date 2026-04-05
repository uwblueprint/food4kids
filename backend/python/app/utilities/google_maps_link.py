from typing import TYPE_CHECKING
from urllib.parse import quote

if TYPE_CHECKING:
    from app.models.location import Location


def build_google_maps_directions_url(
    locations: list["Location"],
    warehouse_lat: float,
    warehouse_lon: float,
) -> str:
    """Build a Google Maps directions URL for a route.

    The URL follows the format:
        https://www.google.com/maps/dir/{origin}/{stop1}/{stop2}/...

    Each stop is represented by its address (URL-encoded), falling back to
    raw ``lat,lon`` coordinates when no address is available.

    Args:
        locations: Ordered list of Location objects (route stops).
        warehouse_lat: Latitude of the warehouse (route origin).
        warehouse_lon: Longitude of the warehouse (route origin).

    Returns:
        A fully-formed Google Maps directions URL string.

    Raises:
        ValueError: If a location has neither an address nor coordinates.
    """
    base_url = "https://www.google.com/maps/dir"

    # Origin is always the warehouse coordinates
    segments: list[str] = [f"{warehouse_lat},{warehouse_lon}"]

    for i, location in enumerate(locations):
        if location.address:
            segments.append(quote(location.address, safe=""))
        elif location.latitude is not None and location.longitude is not None:
            segments.append(f"{location.latitude},{location.longitude}")
        else:
            raise ValueError(
                f"Stop {i + 1} has neither an address nor coordinates."
            )

    return base_url + "/" + "/".join(segments)
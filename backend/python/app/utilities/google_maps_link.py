from dataclasses import dataclass
from urllib.parse import quote


@dataclass
class MapWaypoint:
    """A single resolved stop for a directions URL.

    Decoupled from the ``Location`` model so callers can pass whatever the
    route actually delivered to — e.g. a frozen snapshot's address/coords for
    a past route, or the live location's for an upcoming one.
    """

    address: str | None
    latitude: float | None
    longitude: float | None


def build_google_maps_directions_url(
    stops: list[MapWaypoint],
    warehouse_lat: float,
    warehouse_lon: float,
) -> str:
    """Build a Google Maps directions URL for a route.

    The URL follows the format:
        https://www.google.com/maps/dir/{origin}/{stop1}/{stop2}/...

    Each stop is represented by its address (URL-encoded), falling back to
    raw ``lat,lon`` coordinates when no address is available.

    Google Maps ``/dir/`` URLs support a maximum of 50 waypoints (excluding
    the origin).  Browsers generally refuse URLs longer than ~2 000
    characters.  Both limits are enforced here.

    Args:
        stops: Ordered list of resolved waypoints (route stops).
        warehouse_lat: Latitude of the warehouse (route origin).
        warehouse_lon: Longitude of the warehouse (route origin).

    Returns:
        A fully-formed Google Maps directions URL string.

    Raises:
        ValueError: If a stop has neither an address nor coordinates,
            if there are more than 50 stops, or if the resulting URL
            exceeds 2 000 characters.
    """
    _MAX_WAYPOINTS = 50
    _MAX_URL_LENGTH = 2000

    if len(stops) > _MAX_WAYPOINTS:
        raise ValueError(
            f"Route has {len(stops)} stops, but Google Maps directions "
            f"URLs support a maximum of {_MAX_WAYPOINTS} waypoints."
        )

    base_url = "https://www.google.com/maps/dir"

    # Origin is always the warehouse coordinates
    segments: list[str] = [f"{warehouse_lat},{warehouse_lon}"]

    for i, stop in enumerate(stops):
        if stop.address:
            segments.append(quote(stop.address, safe=""))
        elif stop.latitude is not None and stop.longitude is not None:
            segments.append(f"{stop.latitude},{stop.longitude}")
        else:
            raise ValueError(f"Stop {i + 1} has neither an address nor coordinates.")

    url = base_url + "/" + "/".join(segments)

    if len(url) > _MAX_URL_LENGTH:
        raise ValueError(
            f"Generated URL is {len(url)} characters, which exceeds the "
            f"browser limit of {_MAX_URL_LENGTH} characters."
        )

    return url

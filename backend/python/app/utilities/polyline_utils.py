"""Utility functions for encoding and decoding polylines using the polyline library."""

from typing import TypeAlias, cast

import polyline  # type: ignore[import-untyped]

# Type aliases for coordinate representations
# Google Maps API uses (lat, lon) order
Coordinate: TypeAlias = tuple[float, float]
CoordinateList: TypeAlias = list[Coordinate]


def encode_polyline(coordinates: CoordinateList, precision: int = 5) -> str:
    """Encodes a list of coordinates into a polyline string.
    Args:
        coordinates (CoordinateList): List of (latitude, longitude) tuples.
        precision (int, optional): The precision of the encoding. Defaults to 5.
    Returns:
        str: Encoded polyline string.
    """
    result: str = polyline.encode(coordinates, precision=precision)
    return result


def decode_polyline(polyline_str: str, precision: int = 5) -> CoordinateList:
    """Decodes a polyline string into a list of coordinates.
    Args:
        polyline_str (str): Encoded polyline string.
        precision (int, optional): The precision of the encoding. Defaults to 5.
    Returns:
        CoordinateList: List of (latitude, longitude) tuples.
    """
    result: CoordinateList = cast(
        "CoordinateList", polyline.decode(polyline_str, precision=precision)
    )
    return result

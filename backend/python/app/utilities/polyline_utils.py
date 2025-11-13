"""Utility functions for encoding and decoding polylines using the polyline library."""

from typing import TypeAlias

import polyline

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
    return polyline.encode(coordinates, precision=precision)


def decode_polyline(polyline_str: str, precision: int = 5) -> CoordinateList:
    """Decodes a polyline string into a list of coordinates.
    Args:
        polyline_str (str): Encoded polyline string.
        precision (int, optional): The precision of the encoding. Defaults to 5.
    Returns:
        CoordinateList: List of (latitude, longitude) tuples.
    """
    return polyline.decode(polyline_str, precision=precision)


# Example usage and testing
if __name__ == "__main__":
    # Test with Google Maps coordinate order (lat, lon)
    print("Testing with Google Maps (lat, lon) format:")
    test_coords = [(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)]
    print(f"Original coordinates: {test_coords}")

    encoded = encode_polyline(test_coords)
    print(f"Encoded polyline: {encoded}")

    decoded = decode_polyline(encoded)
    print(f"Decoded coordinates: {decoded}")
    print()

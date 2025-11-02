import os
import re
from dataclasses import dataclass

import googlemaps

GEOCODING_API_KEY = os.getenv("GEOCODING_API_KEY")
REGION_BIAS = "ca"


@dataclass
class GeocodeResult:
    latitude: float
    longitude: float


class GoogleMapsClient:
    """Google Maps API client using official Python client"""

    def __init__(self, api_key: str = GEOCODING_API_KEY) -> None:
        self.client: GoogleMapsClient = googlemaps.Client(key=api_key)

    async def geocode_address(self, address: str) -> GeocodeResult | None:
        """Geocode a single address string using Google Maps Geocoding API"""
        cleaned_address = self._clean_address(address)
        geocode_result = self.client.geocode(cleaned_address, region=REGION_BIAS)

        if geocode_result:
            location = geocode_result[0]["geometry"]["location"]
            return GeocodeResult(latitude=location["lat"], longitude=location["lng"])
        return None

    def _clean_address(self, address: str) -> str:
        """Cleans address string to improve geocoding accuracy with Google Maps API"""
        # remove whitespace, newlines, commas
        address = address.strip().replace("\n", " ").replace("\r", "").replace(",", "")

        # remove unit/apartment/suite numbers
        address = re.sub(
            r"\b(?:Unit|Apt|Suite|#)\s*\w+\b", "", address, flags=re.IGNORECASE
        )

        # remove extra spaces
        address = re.sub(r"\s+", " ", address)
        return address

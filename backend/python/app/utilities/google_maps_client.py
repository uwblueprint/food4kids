import logging
import re
from dataclasses import dataclass

from googlemaps import Client  # type: ignore


@dataclass
class GeocodeResult:
    formatted_address: str
    place_id: str
    latitude: float
    longitude: float


class GoogleMapsClient:
    """Google Maps API client using official Python client"""

    def __init__(self, logger: logging.Logger, api_key: str, region_bias: str = "ca") -> None:
        self.logger = logger
        self.client: Client = Client(key=api_key)
        self.region_bias = region_bias

    async def geocode_address(self, address: str) -> GeocodeResult | None:
        """Geocode a single address string using Google Maps Geocoding API"""
        try:
            cleaned_address = self._clean_address(address)
            geocode_result = self.client.geocode(
                cleaned_address, region=self.region_bias)

            if geocode_result:
                location = geocode_result[0]["geometry"]["location"]
                return GeocodeResult(
                    formatted_address=geocode_result[0]["formatted_address"],
                    place_id=geocode_result[0]["place_id"],
                    latitude=location["lat"],
                    longitude=location["lng"]
                )
            return None
        except Exception as e:
            raise e

    async def geocode_addresses(self, addresses: list[str]) -> list[GeocodeResult | None]:
        """
        Accepts a list of strings representing addresses
        Returns a list of GeocodeResult for each address
        If address is invalid, there will be None instead
        Example Usage:
        test = ["200 University Ave West, Waterloo, Ontario", "InvalidAddress"]
        Resulting output: [{'latitude': 43.4729399, 'longitude': -80.54007159999999}, None]
        """
        return [await self.geocode_address(address) for address in addresses]

    def _clean_address(self, address: str) -> str:
        """Cleans address string to improve geocoding accuracy with Google Maps API"""
        # remove whitespace, newlines, commas
        address = address.strip().replace("\n", " ").replace("\r", "").replace(",", "")

        # remove extra spaces
        address = re.sub(r"\s+", " ", address)
        return address

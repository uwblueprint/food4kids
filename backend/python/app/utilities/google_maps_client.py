import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any

import googlemaps  # type: ignore[import-untyped]


@dataclass
class GeocodeResult:
    formatted_address: str
    place_id: str
    latitude: float
    longitude: float
    is_precise: bool


IMPRECISE_LOCATION_TYPE = "APPROXIMATE"


def is_precise_geocode_result(result: dict[str, Any]) -> bool:
    """True when a geocoder result identifies a specific street address.

    Google answers almost any input with a successful match, falling back to
    whatever it can find: "99999 Nonexistent Pkwy, Blandford Township" resolves
    to the township centroid, a misspelled street resolves to the city, and a
    bare postal code resolves to the middle of the delivery area. All of those
    arrive as ordinary OK results, so a caller that only checks for None accepts
    them and ends up sending a driver to a field.

    A house we can deliver to always carries a street_number component and is
    located more precisely than APPROXIMATE. Both conditions are needed —
    neither alone is sufficient. Also rejects PO boxes and bare rural-route
    addresses, which are real address formats but not places a driver can find.

    Verified against real Waterloo Region addresses, urban and rural, including
    apartments and unit numbers; test_google_maps_geocode_precision.py holds the
    recorded response shapes.
    """
    component_types = {
        component_type
        for component in result["address_components"]
        for component_type in component["types"]
    }
    if "street_number" not in component_types:
        return False
    location_type: str = result["geometry"]["location_type"]
    return location_type != IMPRECISE_LOCATION_TYPE


class GoogleMapsClient:
    """Google Maps API client using official Python client"""

    def __init__(
        self, logger: logging.Logger, api_key: str, region_bias: str = "ca"
    ) -> None:
        self.logger = logger
        self.client: googlemaps.Client = googlemaps.Client(key=api_key)
        self.region_bias = region_bias

    async def geocode_address(self, address: str) -> GeocodeResult | None:
        """Geocode a single address string using Google Maps Geocoding API"""
        return await asyncio.to_thread(self._geocode_address_sync, address)

    def _geocode_address_sync(self, address: str) -> GeocodeResult | None:
        cleaned_address = self._clean_address(address)
        geocode_result = self.client.geocode(cleaned_address, region=self.region_bias)

        if geocode_result:
            top = geocode_result[0]
            location = top["geometry"]["location"]
            return GeocodeResult(
                formatted_address=top["formatted_address"],
                place_id=top["place_id"],
                latitude=location["lat"],
                longitude=location["lng"],
                is_precise=is_precise_geocode_result(top),
            )
        return None

    async def geocode_addresses(
        self, addresses: list[str]
    ) -> list[GeocodeResult | None]:
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

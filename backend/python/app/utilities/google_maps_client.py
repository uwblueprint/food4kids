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

    Google returns an OK result for almost anything — a nonexistent street
    number resolves to the township centroid — so "got a result" is not enough.
    A house we can deliver to has both a street_number component and a
    location_type better than APPROXIMATE; neither alone is sufficient. Also
    rejects PO boxes and bare rural routes, which no driver can find.

    ``partial_match`` is Google's own "this is not what you asked for" flag —
    set when the geocoder had to drop or guess part of the query (a misspelled
    street, an address that exists on a same-named street in another town). It
    is omitted entirely on an exact match, so its absence means a clean hit.
    """
    if result.get("partial_match", False):
        return False
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

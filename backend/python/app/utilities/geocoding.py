import asyncio
import os
from dataclasses import dataclass
from typing import Any

import httpx

GEOCODING_API_KEY = os.getenv("GEOCODING_API_KEY")


@dataclass
class GeocodeResult:
    latitude: float
    longitude: float


async def geocode(address: str) -> GeocodeResult:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": GEOCODING_API_KEY},
        )
        data: dict[str, Any] = response.json()
        if data["status"] == "OK":
            location = data["results"][0]["geometry"]["location"]
            geocode_result = GeocodeResult(
                latitude=location["lat"],
                longitude=location["lng"]
            )
            await asyncio.sleep(0.2)  # TODO: fix rate limiting?
            return geocode_result
        raise Exception(
            f"Geocoding failed for address: {address}")


async def geocode_addresses(addresses: list[str]) -> list[dict[str, float] | None]:
    """
    Accepts a list of strings representing addresses
    Returns a list of {"lat": ..., "lng": ...} one to one for each address
    If address is invalid, there will be None instead

    Example Usage:
    test = ["200 University Ave West, Waterloo, Ontario", "InvalidAddress"]
    results = asyncio.run(geocode_addresses(test))
    print(results)
    Resulting output: [{'lat': 43.4729399, 'lng': -80.54007159999999}, None]
    """
    tasks = [geocode(address) for address in addresses]
    return await asyncio.gather(*tasks)

import asyncio
import os

import httpx

GEOCODING_API_KEY = os.getenv("GEOCODING_API_KEY")


async def geocode(address: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": GEOCODING_API_KEY},
        )
        data = response.json()
        if data["status"] == "OK":
            return data["results"][0]["geometry"]["location"]
        return None


# Accepts a list of strings representing addresses
# Returns a list of {"lat": ..., "lng": ...} one to one for each address
# If address is invalid, there will be None instead
async def geocode_addresses(addresses: list) -> list:
    tasks = [geocode(address) for address in addresses]
    return await asyncio.gather(*tasks)


# test = ["200 University Ave West, Waterloo, Ontario", "InvalidAddress"]
# results = asyncio.run(geocode_addresses(test))
# print(results)

# Resulting output: [{'lat': 43.4729399, 'lng': -80.54007159999999}, None]

import os

import httpx

OSRM_BASE_URL = os.getenv("OSRM_BASE_URL", "http://router.project-osrm.org")


async def get_osrm_time_matrix(coords: list[tuple[float, float]]) -> list[list[float]]:
    if not coords:
        return []
    if len(coords) == 1:
        return [[0.0]]

    coordinates = ";".join([f"{lon},{lat}" for lat, lon in coords])
    url = f"{OSRM_BASE_URL}/table/v1/driving/{coordinates}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params={"annotations": "duration"})
        response.raise_for_status()
        data = response.json()

        if data.get("code") != "Ok":
            raise ValueError(f"OSRM error: {data.get('message', 'Unknown error')}")

        durations = data.get("durations")
        if not durations:
            raise ValueError("Missing durations in response")

        return [
            [float("inf") if v is None else float(v) for v in row]
            for row in durations
        ]
"""Demo script: Google Maps Link generation endpoint.

Run inside Docker:
    docker-compose exec backend python scripts/demo_google_maps_link.py

Prerequisites:
    - Backend server is running on port 8080

The script:
    1. Creates real Waterloo-area locations, a route, route stops, and
       system settings (warehouse) directly via SQLAlchemy
    2. Calls GET /routes/{route_id}/google-maps-link
    3. Prints the generated URL so you can open it in a browser
    4. Cleans up all created rows (even on error)
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timezone

import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_BASE = "http://localhost:8080"
DATABASE_URL = "postgresql://postgres:postgres@db:5432/f4k"

WAREHOUSE_LAT = 43.4731832
WAREHOUSE_LON = -80.5397772

# Real Waterloo/Kitchener locations for a realistic demo
DEMO_LOCATIONS = [
    {
        "contact_name": "Bogda Restaurant",
        "address": "62 Balsam St unit B-103, Waterloo, ON N2L 3H2",
        "phone_number": "(519) 555-0001",
        "latitude": 43.4764456,
        "longitude": -80.5300104,
    },
    {
        "contact_name": "Exclamation Waterloo",
        "address": "63 Hickory St W, Waterloo, ON N2L 0J1",
        "phone_number": "(519) 555-0002",
        "latitude": 43.4772111,
        "longitude": -80.5309449,
    },
    {
        "contact_name": "The Humble Lotus",
        "address": "388 King St E, Kitchener, ON N2G 0C6",
        "phone_number": "(519) 555-0003",
        "latitude": 43.4473068,
        "longitude": -80.4826182,
    },
]


def main() -> None:
    engine = create_engine(DATABASE_URL, echo=False)
    now = datetime.now(timezone.utc)

    # IDs for cleanup
    route_id = uuid.uuid4()
    location_ids: list[uuid.UUID] = []
    system_settings_id = uuid.uuid4()

    with Session(engine) as session:
        try:
            # ----------------------------------------------------------
            # 1. Create system settings (warehouse coordinates)
            # ----------------------------------------------------------
            session.execute(
                text(
                    """
                    INSERT INTO system_settings
                        (system_settings_id, warehouse_latitude, warehouse_longitude,
                         warehouse_location, created_at)
                    VALUES (:id, :lat, :lon, :loc, :now)
                    """
                ),
                {
                    "id": system_settings_id,
                    "lat": WAREHOUSE_LAT,
                    "lon": WAREHOUSE_LON,
                    "loc": "Waterloo, ON",
                    "now": now,
                },
            )
            print(f"Created system settings ({system_settings_id})")

            # ----------------------------------------------------------
            # 2. Create locations
            # ----------------------------------------------------------
            for loc_data in DEMO_LOCATIONS:
                loc_id = uuid.uuid4()
                location_ids.append(loc_id)
                session.execute(
                    text(
                        """
                        INSERT INTO locations
                            (location_id, contact_name, address, phone_number,
                             latitude, longitude, halal, num_boxes, notes,
                             dietary_restrictions, state, created_at)
                        VALUES
                            (:id, :contact, :addr, :phone,
                             :lat, :lon, false, 5, '',
                             '', 'ACTIVE', :now)
                        """
                    ),
                    {
                        "id": loc_id,
                        "contact": loc_data["contact_name"],
                        "addr": loc_data["address"],
                        "phone": loc_data["phone_number"],
                        "lat": loc_data["latitude"],
                        "lon": loc_data["longitude"],
                        "now": now,
                    },
                )

            print(f"Created {len(location_ids)} locations")

            # ----------------------------------------------------------
            # 3. Create route
            # ----------------------------------------------------------
            session.execute(
                text(
                    """
                    INSERT INTO routes (route_id, name, notes, length, created_at)
                    VALUES (:id, :name, :notes, :length, :now)
                    """
                ),
                {
                    "id": route_id,
                    "name": "Demo Google Maps Route",
                    "notes": "Created by demo_google_maps_link.py",
                    "length": 7.3,
                    "now": now,
                },
            )
            print(f"Created route ({route_id})")

            # ----------------------------------------------------------
            # 4. Create route stops
            # ----------------------------------------------------------
            for stop_num, loc_id in enumerate(location_ids, 1):
                session.execute(
                    text(
                        """
                        INSERT INTO route_stops
                            (route_stop_id, route_id, location_id, stop_number, created_at)
                        VALUES (:rsid, :rid, :lid, :sn, :now)
                        """
                    ),
                    {
                        "rsid": uuid.uuid4(),
                        "rid": route_id,
                        "lid": loc_id,
                        "sn": stop_num,
                        "now": now,
                    },
                )

            print(f"Created {len(location_ids)} route stops")
            session.commit()

            # ----------------------------------------------------------
            # 5. Call the endpoint
            # ----------------------------------------------------------
            print("\n" + "=" * 60)
            url = f"{API_BASE}/routes/{route_id}/google-maps-link"
            print(f"GET {url}")

            resp = requests.get(url, timeout=10)
            print(f"Status: {resp.status_code}")

            if resp.status_code == 200:
                url = resp.json()
                print(f"\nGoogle Maps URL:\n{url}")
                print(
                    "\n^ Open this link in a browser to see the route on Google Maps."
                )
            else:
                print(f"Error: {resp.text}")
                sys.exit(1)

        finally:
            # ----------------------------------------------------------
            # 6. Cleanup — always runs, even on error
            # ----------------------------------------------------------
            print("\n" + "=" * 60)
            print("Cleaning up demo data...")

            session.execute(
                text("DELETE FROM route_stops WHERE route_id = :rid"),
                {"rid": route_id},
            )
            session.execute(
                text("DELETE FROM routes WHERE route_id = :rid"),
                {"rid": route_id},
            )
            for loc_id in location_ids:
                session.execute(
                    text("DELETE FROM locations WHERE location_id = :lid"),
                    {"lid": loc_id},
                )
            session.execute(
                text(
                    "DELETE FROM system_settings WHERE system_settings_id = :id"
                ),
                {"id": system_settings_id},
            )

            session.commit()
            print("Cleanup complete.")


if __name__ == "__main__":
    main()
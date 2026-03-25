"""
Demo script for PATCH /routes/{route_id} endpoint.

Creates an initial route directly in the DB (same pattern as seed_database.py),
then tests three PATCH scenarios via HTTP:

  1. Add a stop to the END of a route
  2. Add a stop in the MIDDLE of a route
  3. Remove a stop from the MIDDLE of a route

Each scenario prints the before/after encoded polyline, which can be
decoded at:
  https://developers.google.com/maps/documentation/utilities/polylineutility

Usage (run inside the backend container):
    docker-compose exec backend python scripts/demo_patch_route.py

Requirements:
    - Backend running on localhost:8080
    - Valid Google Maps API key configured in the backend
"""

import sys
import uuid
from pathlib import Path

# Add the backend root (/app) to sys.path so "app.models" is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from sqlmodel import Session, create_engine

# ---------------------------------------------------------------------------
# DB connection — same URL as seed_database.py
# ---------------------------------------------------------------------------
DATABASE_URL = "postgresql://postgres:postgres@f4k_db:5432/f4k"

BASE_URL = "http://localhost:8080"

# ---------------------------------------------------------------------------
# Waterloo Region locations for demo
# ---------------------------------------------------------------------------
STOP_DATA = [
    {
        "name": "Stop A - Waterloo Public Library",
        "address": "35 Albert St, Waterloo, ON N2L 5E2",
        "phone_number": "+15198862700",
        "latitude": 43.4668,
        "longitude": -80.5164,
    },
    {
        "name": "Stop B - Waterloo City Hall",
        "address": "100 Regina St S, Waterloo, ON N2J 4A8",
        "phone_number": "+15198867600",
        "latitude": 43.4651,
        "longitude": -80.5223,
    },
    {
        "name": "Stop C - University of Waterloo",
        "address": "200 University Ave W, Waterloo, ON N2L 3G1",
        "phone_number": "+15198884567",
        "latitude": 43.4723,
        "longitude": -80.5449,
    },
    {
        "name": "Stop D - Conestoga Mall",
        "address": "550 King St N, Waterloo, ON N2L 5W6",
        "phone_number": "+15198856770",
        "latitude": 43.4940,
        "longitude": -80.5207,
    },
    {
        "name": "Stop E - RIM Park",
        "address": "2001 University Ave E, Waterloo, ON N2K 4K4",
        "phone_number": "+15197472600",
        "latitude": 43.5018,
        "longitude": -80.4686,
    },
]


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def ensure_system_settings(session: Session) -> None:
    """Ensure a system_settings row exists with warehouse coordinates."""
    from app.models.system_settings import SystemSettings

    existing = session.query(SystemSettings).first()
    if not existing:
        session.add(SystemSettings(
            warehouse_location="137 Glasgow St, Kitchener, ON N2G 4X8",
            warehouse_latitude=43.4516,
            warehouse_longitude=-80.4925,
        ))
        session.commit()


def create_locations_and_route(session: Session) -> tuple[list[uuid.UUID], uuid.UUID]:
    """Create 5 demo locations + an initial route A->B->C->D in the DB."""
    from app.models.location import Location
    from app.models.route import Route
    from app.models.route_stop import RouteStop

    # Create locations
    locations = []
    for stop in STOP_DATA:
        loc = Location(
            contact_name=stop["name"],
            address=stop["address"],
            phone_number=stop["phone_number"],
            latitude=stop["latitude"],
            longitude=stop["longitude"],
            halal=False,
            num_boxes=1,
            notes="",
            dietary_restrictions="",
        )
        session.add(loc)
        locations.append(loc)

    session.flush()  # populate location_ids before creating stops

    loc_a, loc_b, loc_c, loc_d, loc_e = locations

    # Create initial route A -> B -> C -> D (no polyline yet — PATCH will generate it)
    route = Route(
        name="Demo Route",
        notes="Created by demo_patch_route.py",
        length=0.0,
    )
    session.add(route)
    session.flush()

    for i, loc in enumerate([loc_a, loc_b, loc_c, loc_d], start=1):
        session.add(RouteStop(
            route_id=route.route_id,
            location_id=loc.location_id,
            stop_number=i,
        ))

    session.commit()

    return [loc.location_id for loc in locations], route.route_id


def cleanup(session: Session, location_ids: list[uuid.UUID], route_id: uuid.UUID) -> None:
    """Delete all demo data from the DB."""
    from app.models.location import Location
    from app.models.route import Route

    route = session.get(Route, route_id)
    if route:
        session.delete(route)

    for lid in location_ids:
        loc = session.get(Location, lid)
        if loc:
            session.delete(loc)

    session.commit()


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def patch_route(route_id: uuid.UUID, location_ids: list[uuid.UUID]) -> dict:
    resp = requests.patch(
        f"{BASE_URL}/routes/{route_id}",
        json={"location_ids": [str(lid) for lid in location_ids]},
    )
    resp.raise_for_status()
    return resp.json()


def print_route(label: str, route: dict) -> None:
    print(f"\n  [{label}]")
    print(f"  Length  : {route['length']:.2f} km")
    print(f"  Polyline: {route['encoded_polyline']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("PATCH /routes/{route_id} - Demo Script")
    print("=" * 60)

    engine = create_engine(DATABASE_URL, echo=False)

    with Session(engine) as session:
        print("\n[Setup] Ensuring system settings exist...")
        ensure_system_settings(session)
        print("\n[Setup] Creating 5 demo locations and initial route A->B->C->D in DB...")
        location_ids, route_id = create_locations_and_route(session)
        loc_a, loc_b, loc_c, loc_d, loc_e = location_ids
        print(f"  Route ID   : {route_id}")
        print(f"  Location A : {loc_a}")
        print(f"  Location B : {loc_b}")
        print(f"  Location C : {loc_c}")
        print(f"  Location D : {loc_d}")
        print(f"  Location E : {loc_e}")

        try:
            # Scenario 1: Add E to the end
            print("\n" + "=" * 60)
            print("Scenario 1: Add stop E to the END")
            print("  Before: A -> B -> C -> D")
            print("  After : A -> B -> C -> D -> E")
            print("=" * 60)
            result = patch_route(route_id, [loc_a, loc_b, loc_c, loc_d, loc_e])
            print_route("After adding E to end", result)

            # Scenario 2: Add E in the middle
            print("\n" + "=" * 60)
            print("Scenario 2: Add stop E in the MIDDLE (between B and C)")
            print("  Before: A -> B -> C -> D")
            print("  After : A -> B -> E -> C -> D")
            print("=" * 60)
            result = patch_route(route_id, [loc_a, loc_b, loc_e, loc_c, loc_d])
            print_route("After adding E in middle", result)

            # Scenario 3: Remove B from the middle
            print("\n" + "=" * 60)
            print("Scenario 3: Remove stop B from the MIDDLE")
            print("  Before: A -> B -> C -> D")
            print("  After : A -> C -> D")
            print("=" * 60)
            result = patch_route(route_id, [loc_a, loc_c, loc_d])
            print_route("After removing B from middle", result)

            print("\n" + "=" * 60)
            print("Demo complete!")
            print("Paste the polyline strings above into:")
            print("https://developers.google.com/maps/documentation/utilities/polylineutility")
            print("=" * 60)

        finally:
            print("\n[Cleanup] Removing demo data from DB...")
            cleanup(session, location_ids, route_id)
            print("  Done.")


if __name__ == "__main__":
    main()
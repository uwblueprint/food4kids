#!/usr/bin/env python3
"""
Test script for Sweep clustering with real database locations.

Run from backend/python (or from repo root with PYTHONPATH=backend/python):
  python -m app.services.implementations.sweep_algorithm_test

Or run this file directly (from any directory):
  python backend/python/app/services/implementations/sweep_algorithm_test.py
"""

import os
import sys

# Ensure the backend root is on path so "app" is importable (works when run as script or -m)
_backend_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir)
)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from sqlmodel import Session, create_engine, func, select

from app.models.location import Location
from app.models.location_group import LocationGroup  # noqa: F401
from app.models.route import Route  # noqa: F401
from app.models.route_group import RouteGroup  # noqa: F401
from app.models.route_group_membership import RouteGroupMembership  # noqa: F401
from app.models.route_stop import RouteStop  # noqa: F401
from app.models.system_settings import SystemSettings
from app.services.implementations.sweep_clustering import (
    SweepClusteringAlgorithm,
)
from app.utilities.geocoding import geocode

# Use the same connection string as seed_database.py
DATABASE_URL = "postgresql://postgres:postgres@f4k_db:5432/f4k"

# Configure number of locations pulled from csv for testing
LOCATIONS_COUNT = 18

# Sweep clustering uses these in the loop; both must be set (use high box limit to avoid splitting by boxes).
NUM_CLUSTERS = 10
MAX_LOCATIONS_PER_CLUSTER = 10
MAX_BOXES_PER_CLUSTER = 9999


async def main() -> None:
    engine = create_engine(DATABASE_URL, echo=False)

    with Session(engine) as session:
        # Fetch locations that have coordinates
        statement = (
            select(Location)
            .where(Location.latitude is not None, Location.longitude is not None)
            .order_by(func.random())
            .limit(LOCATIONS_COUNT)
        )

        locations = list(session.exec(statement).all())

        print(f"Fetched {len(locations)} locations from database\n")

        if len(locations) < 2:
            print("Not enough locations with coordinates to cluster!")
            return

        # Warehouse coordinates: from SystemSettings (lat/lon or geocode address) or centroid fallback
        warehouse_lat: float
        warehouse_lon: float
        system_settings = session.exec(select(SystemSettings).limit(1)).first()
        if (
            system_settings
            and system_settings.warehouse_latitude is not None
            and system_settings.warehouse_longitude is not None
        ):
            warehouse_lat = system_settings.warehouse_latitude
            warehouse_lon = system_settings.warehouse_longitude
            print(f"Using warehouse from system settings: ({warehouse_lat}, {warehouse_lon})\n")
        elif system_settings and system_settings.warehouse_location:
            coords = await geocode(system_settings.warehouse_location)
            if coords is not None:
                warehouse_lat = coords["lat"]
                warehouse_lon = coords["lng"]
                print(f"Geocoded warehouse: ({warehouse_lat}, {warehouse_lon})\n")
            else:
                warehouse_lat = sum(loc.latitude for loc in locations) / len(locations)
                warehouse_lon = sum(loc.longitude for loc in locations) / len(locations)
                print(f"Geocode failed; using centroid: ({warehouse_lat}, {warehouse_lon})\n")
        else:
            warehouse_lat = sum(loc.latitude for loc in locations) / len(locations)
            warehouse_lon = sum(loc.longitude for loc in locations) / len(locations)
            print(f"No warehouse in system settings; using centroid: ({warehouse_lat}, {warehouse_lon})\n")

        total_boxes = sum(loc.num_boxes for loc in locations)

        print("Locations to cluster:")
        print("-" * 60)
        for loc in locations:
            name = loc.school_name or loc.contact_name
            print(f"  {name}")
            print(f"    Address: {loc.address}")
            print(f"    Coords: ({loc.latitude}, {loc.longitude})")
            print(f"    Boxes: {loc.num_boxes}")
            print()

        print("Total number of boxes: ", total_boxes)
        print("Total locations: ", len(locations))

        clustering_algo = SweepClusteringAlgorithm()

        print("Running Sweep clustering:")
        print(f"  - Number of clusters: {NUM_CLUSTERS}")
        print(f"  - Max locations per cluster: {MAX_LOCATIONS_PER_CLUSTER}")
        print(f"  - Max boxes per cluster: {MAX_BOXES_PER_CLUSTER}")
        print("-" * 60)

        try:
            clusters = await clustering_algo.cluster_locations(
                locations=locations,
                num_clusters=NUM_CLUSTERS,
                warehouse_lat=warehouse_lat,
                warehouse_lon=warehouse_lon,
                max_locations_per_cluster=MAX_LOCATIONS_PER_CLUSTER,
                max_boxes_per_cluster=MAX_BOXES_PER_CLUSTER,
                timeout_seconds=30.0,
            )

            print("\nClustering Results:")
            print("=" * 60)

            df_rows = []
            for i, cluster in enumerate(clusters):
                print(f"\nCluster {i + 1} ({len(cluster)} locations):")
                print("-" * 40)

                if not cluster:
                    print("  (empty cluster)")
                    continue

                cluster_boxes = 0
                for loc in cluster:
                    name = loc.school_name or loc.contact_name
                    print(f"  • {name}")
                    print(f"    {loc.address}")
                    print(f"    Coords: ({loc.latitude}, {loc.longitude})")
                    print(f"    Boxes: {loc.num_boxes}")
                    cluster_boxes += loc.num_boxes
                    df_rows.append(
                        {"name": name, "long": loc.longitude, "lat": loc.latitude, "group": i}
                    )

                print(f"\n  Total boxes in cluster: {cluster_boxes}")

            if df_rows:
                df = pd.DataFrame(data=df_rows)
                sns.scatterplot(data=df, x="long", y="lat", hue="group", palette="Set2")
                plt.title(
                    f"Generated Sweep clustering for {len(locations)} locations with {len(clusters)} clusters"
                )
                plt.xlabel("Longitude")
                plt.ylabel("Latitude")
                output_dir = "./app/data"
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                plt.savefig(
                    os.path.join(output_dir, "sweep_clustering_test.png"),
                    dpi=300,
                    bbox_inches="tight",
                )

            print("\n" + "=" * 60)
            print("Summary:")
            print(f"  Total clusters: {len(clusters)}")
            print(f"  Number of locations in each cluster: {[len(c) for c in clusters]}")
            print(f"  Total locations clustered: {sum(len(c) for c in clusters)}")

        except ValueError as e:
            print(f"Clustering failed: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

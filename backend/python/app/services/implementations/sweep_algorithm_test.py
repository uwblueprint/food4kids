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

sys.path.insert(0, "/app")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sqlmodel import Session, create_engine, func, select

from app.models.location import Location
from app.models.route_stop import RouteStop  # noqa: F401
from app.models.system_settings import SystemSettings
from app.services.implementations.sweep_clustering import SweepClusteringAlgorithm

# Use the same connection string as seed_database.py
DATABASE_URL = "postgresql://postgres:postgres@f4k_db:5432/f4k"

# Configure number of locations pulled from csv for testing
LOCATIONS_COUNT = 18

NUM_CLUSTERS = 10
MAX_LOCATIONS_PER_CLUSTER = 5
MAX_BOXES_PER_CLUSTER = 50


def _print_and_collect_rows(clusters: list[list[Location]]) -> list[dict]:
    df_rows: list[dict] = []
    for index, cluster in enumerate(clusters):
        print(f"\nCluster {index + 1} ({len(cluster)} locations):")
        print("-" * 40)

        if not cluster:
            print("  (empty cluster)")
            continue

        cluster_boxes = 0
        for location in cluster:
            name = location.school_name or location.contact_name
            print(f"  • {name}")
            print(f"    {location.address}")
            print(f"    Coords: ({location.latitude}, {location.longitude})")
            print(f"    Boxes: {location.num_boxes}")
            cluster_boxes += location.num_boxes
            df_rows.append(
                {
                    "name": name,
                    "long": location.longitude,
                    "latitude": location.latitude,
                    "group": index,
                }
            )

        print(f"\n  Total boxes in cluster: {cluster_boxes}")

    return df_rows


def _save_plot(df_rows: list[dict], title: str, filename: str) -> None:
    if not df_rows:
        return

    df = pd.DataFrame(data=df_rows)
    sns.scatterplot(data=df, x="long", y="lat", hue="group", palette="Set2")
    plt.title(title)
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")

    output_dir = "./app/data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    plt.savefig(
        os.path.join(output_dir, filename),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


async def main() -> None:
    engine = create_engine(DATABASE_URL, echo=False)

    with Session(engine) as session:
        statement = (
            select(Location)
            .where(Location.latitude != None, Location.longitude != None)  # noqa: E711
            .order_by(func.random())
            .limit(LOCATIONS_COUNT)
        )

        locations = list(session.exec(statement).all())

        print(f"Fetched {len(locations)} locations from database\n")

        if len(locations) < 2:
            print("Not enough locations with coordinates to cluster!")
            return

        system_settings = session.exec(select(SystemSettings).limit(1)).first()
        if system_settings is None:
            raise RuntimeError("No SystemSettings row found in the database.")

        warehouse_lat_opt = system_settings.warehouse_latitude
        warehouse_lon_opt = system_settings.warehouse_longitude
        if warehouse_lat_opt is None or warehouse_lon_opt is None:
            raise RuntimeError(
                "Warehouse latitude/longitude is missing in SystemSettings."
            )

        warehouse_lat: float = warehouse_lat_opt
        warehouse_lon: float = warehouse_lon_opt

        print(
            f"Using warehouse from system settings: ({warehouse_lat}, {warehouse_lon})\n"
        )

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

        clustering_algo = SweepClusteringAlgorithm(
            warehouse_lat=warehouse_lat,
            warehouse_lon=warehouse_lon,
        )

        print("\nRunning Sweep clustering (EXACT num_clusters):")
        print(f"  - Number of clusters: {NUM_CLUSTERS}")
        print(f"  - Max locations per cluster: {MAX_LOCATIONS_PER_CLUSTER}")
        print(f"  - Max boxes per cluster: {MAX_BOXES_PER_CLUSTER}")
        print("-" * 60)

        try:
            clusters_exact = await clustering_algo.cluster_locations(
                locations=locations,
                num_clusters=NUM_CLUSTERS,
                max_locations_per_cluster=MAX_LOCATIONS_PER_CLUSTER,
                max_boxes_per_cluster=MAX_BOXES_PER_CLUSTER,
                timeout_seconds=30.0,
            )

            print("\nClustering Results (EXACT num_clusters):")
            print("=" * 60)
            rows_exact = _print_and_collect_rows(clusters_exact)

            _save_plot(
                rows_exact,
                title=(
                    f"Sweep clustering (exact {NUM_CLUSTERS}) for "
                    f"{len(locations)} locations with {len(clusters_exact)} clusters"
                ),
                filename="sweep_clustering_test_exact.png",
            )

            print("\n" + "=" * 60)
            print("Summary (EXACT num_clusters):")
            print(f"  Total clusters: {len(clusters_exact)}")
            print(f"  Locations per cluster: {[len(c) for c in clusters_exact]}")
            print(f"  Total locations clustered: {sum(len(c) for c in clusters_exact)}")

        except ValueError as e:
            print(f"Clustering failed (EXACT num_clusters): {e}")
        except Exception as e:
            print(f"Unexpected error (EXACT num_clusters): {e}")
            import traceback

            traceback.print_exc()

        print("\nRunning Sweep clustering (PACK until constraints hit):")
        print(f"  - Max locations per cluster: {MAX_LOCATIONS_PER_CLUSTER}")
        print(f"  - Max boxes per cluster: {MAX_BOXES_PER_CLUSTER}")
        print("-" * 60)

        try:
            clusters_packed = await clustering_algo.cluster_locations_by_constraints(
                locations=locations,
                max_locations_per_cluster=MAX_LOCATIONS_PER_CLUSTER,
                max_boxes_per_cluster=MAX_BOXES_PER_CLUSTER,
                timeout_seconds=30.0,
            )

            print("\nClustering Results (PACKED):")
            print("=" * 60)
            rows_packed = _print_and_collect_rows(clusters_packed)

            _save_plot(
                rows_packed,
                title=(
                    "Sweep clustering (packed) for "
                    f"{len(locations)} locations with {len(clusters_packed)} clusters"
                ),
                filename="sweep_clustering_test_packed.png",
            )

            print("\n" + "=" * 60)
            print("Summary (PACKED):")
            print(f"  Total clusters: {len(clusters_packed)}")
            print(f"  Locations per cluster: {[len(c) for c in clusters_packed]}")
            print(
                f"  Total locations clustered: {sum(len(c) for c in clusters_packed)}"
            )

        except ValueError as e:
            print(f"Clustering failed (PACKED): {e}")
        except Exception as e:
            print(f"Unexpected error (PACKED): {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

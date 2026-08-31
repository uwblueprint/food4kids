#!/usr/bin/env python3
"""
Developer script for visually testing the KMeans clustering algorithm against
real database locations. Fetches locations from the DB, runs clustering, and
saves a scatter plot to app/data/kmeans_test.png.

Run from backend/python/:
    python scripts/k_means_test.py

Requires a running database (e.g. via docker compose).
Configure the parameters below before running.
"""

import os
import sys

import matplotlib.pyplot as plt
import pandas as pd  # Often useful for data handling
import seaborn as sns

sys.path.insert(0, "/app")

from sqlmodel import Session, create_engine, func, select

# Import all models to register them with SQLModel
from app.models.location import Location
from app.models.location_group import LocationGroup  # noqa: F401
from app.models.route import Route  # noqa: F401
from app.models.route_group import RouteGroup  # noqa: F401
from app.models.route_snapshot import RouteSnapshot  # noqa: F401
from app.models.route_stop import RouteStop  # noqa: F401
from app.models.route_stop_snapshot import RouteStopSnapshot  # noqa: F401
from app.models.system_settings import SystemSettings
from app.services.implementations.k_means_clustering_algorithm import (
    KMeansClusteringAlgorithm,
)
from app.utilities.boxes import compute_boxes

# Use the same connection string as seed_database.py
DATABASE_URL = "postgresql://postgres:postgres@f4k_db:5432/f4k"

# Box sizing and per-car capacity are read from the system_settings row at run
# time — this script clusters against whatever the org has configured.

# Configure number of locations pulled from csv for testing
LOCATIONS_COUNT = 18

# Configure number of clusters to split those locations across
NUM_CLUSTERS = 10


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

        system_settings = session.exec(select(SystemSettings).limit(1)).first()
        if system_settings is None:
            raise RuntimeError("No SystemSettings row found in the database.")

        children_per_box = system_settings.children_per_box
        max_boxes_per_cluster = system_settings.boxes_per_car

        # Count total number of boxes
        total_boxes = 0

        # Print the locations
        print("Locations to cluster:")
        print("-" * 60)
        for loc in locations:
            name = loc.name
            print(f"  {name}")
            print(f"    Address: {loc.address}")
            print(f"    Coords: ({loc.latitude}, {loc.longitude})")
            print(f"    Boxes: {compute_boxes(loc.num_children, children_per_box)}")
            print()
            total_boxes = sum(
                compute_boxes(loc.num_children, children_per_box) for loc in locations
            )

        print("Total number of boxes: ", total_boxes)
        print("Total locations: ", len(locations))

        # Run clustering
        clustering_algo = KMeansClusteringAlgorithm(children_per_box)

        print("Running K-Means clustering:")
        print(f"  - Number of clusters: {NUM_CLUSTERS}")
        print(f"  - Max boxes per cluster: {max_boxes_per_cluster}")
        print("-" * 60)

        try:
            clusters = await clustering_algo.cluster_locations(
                locations=locations,
                num_clusters=NUM_CLUSTERS,
                max_boxes_per_cluster=max_boxes_per_cluster,
                timeout_seconds=30.0,
            )

            # Print results
            print("\nClustering Results:")
            print("=" * 60)

            df_rows = []
            for i, cluster in enumerate(clusters):
                print(f"\nCluster {i + 1} ({len(cluster)} locations):")
                print("-" * 40)

                if not cluster:
                    print("  (empty cluster)")
                    continue

                total_boxes = 0
                for loc in cluster:
                    name = loc.name
                    print(f"  • {name}")
                    print(f"    {loc.address}")
                    print(f"    Coords: ({loc.latitude}, {loc.longitude})")
                    box_count = compute_boxes(loc.num_children, children_per_box)
                    print(f"    Boxes: {box_count}")
                    total_boxes += box_count
                    new_row = {
                        "name": name,
                        "long": loc.longitude,
                        "lat": loc.latitude,
                        "group": i,
                    }
                    df_rows.append(new_row)
            df = pd.DataFrame(data=df_rows)
            sns.scatterplot(data=df, x="long", y="lat", hue="group", palette="Set2")
            plt.title(
                f"Generated K Means classification for {len(locations)} locations with {len(clusters)} clusters"
            )
            plt.xlabel("Longitude")
            plt.ylabel("Latitude")
            output_dir = "./app/data"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            filename = os.path.join(output_dir, "kmeans_test.png")
            plt.savefig(filename, dpi=300, bbox_inches="tight")

            print(f"\n  Total boxes in cluster: {total_boxes}")
            print("\n" + "=" * 60)
            print("Summary:")
            print(f"  Total clusters: {len(clusters)}")
            print(
                f"  Number of locations in each cluster: {[len(c) for c in clusters]}"
            )
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

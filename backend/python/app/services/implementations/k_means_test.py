#!/usr/bin/env python3
"""
Test script for KMeans clustering with real database locations.
Run with: python -m app.services.implementations.k_means_test
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
from app.models.route_group_membership import RouteGroupMembership  # noqa: F401
from app.models.route_stop import RouteStop  # noqa: F401
from app.services.implementations.k_means_clustering_algorithm import (
    KMeansClusteringAlgorithm,
)

# Use the same connection string as seed_database.py
DATABASE_URL = "postgresql://postgres:postgres@f4k_db:5432/f4k"

# Configure number of locations pulled from csv for testing
LOCATIONS_COUNT = 18

# Configure number of clusters + locations per cluster and max boxes per cluster limits
NUM_CLUSTERS = 10
MAX_LOCATIONS_PER_CLUSTER = 10
MAX_BOXES_PER_CLUSTER = None


def main() -> None:
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

        # Count total number of boxes
        total_boxes = 0

        # Print the locations
        print("Locations to cluster:")
        print("-" * 60)
        for loc in locations:
            name = loc.school_name or loc.contact_name
            print(f"  {name}")
            print(f"    Address: {loc.address}")
            print(f"    Coords: ({loc.latitude}, {loc.longitude})")
            print(f"    Boxes: {loc.num_boxes}")
            print()
            total_boxes = sum(loc.num_boxes for loc in locations)

        print("Total number of boxes: ", total_boxes)
        print("Total locations: ", len(locations))

        # Run clustering
        clustering_algo = KMeansClusteringAlgorithm()

        print("Running K-Means clustering:")
        print(f"  - Number of clusters: {NUM_CLUSTERS}")
        print(f"  - Max locations per cluster: {MAX_LOCATIONS_PER_CLUSTER}")
        print(f"  - Max boxes per cluster: {MAX_BOXES_PER_CLUSTER}")
        print("-" * 60)

        try:
            clusters = clustering_algo.cluster_locations(
                locations=locations,
                num_clusters=NUM_CLUSTERS,
                max_locations_per_cluster=MAX_LOCATIONS_PER_CLUSTER,
                max_boxes_per_cluster=MAX_BOXES_PER_CLUSTER,
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
                    name = loc.school_name or loc.contact_name
                    print(f"  • {name}")
                    print(f"    {loc.address}")
                    print(f"    Coords: ({loc.latitude}, {loc.longitude})")
                    print(f"    Boxes: {loc.num_boxes}")
                    total_boxes += loc.num_boxes
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
    main()

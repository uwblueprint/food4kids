#!/usr/bin/env python3
"""
Test script for KMeans clustering with real database locations.
Run with: python -m app.services.implementations.k_means_test
"""

import sys

sys.path.insert(0, "/app")

from sqlmodel import Session, create_engine, select

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


def main() -> None:
    engine = create_engine(DATABASE_URL, echo=False)

    with Session(engine) as session:
        # Fetch locations that have coordinates
        statement = (
            select(Location)
            .where(Location.latitude is not None, Location.longitude is not None)
            .limit(20)
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
        num_clusters = 9
        max_locations_per_cluster = 10
        max_boxes_per_cluster = None

        print("Running K-Means clustering:")
        print(f"  - Number of clusters: {num_clusters}")
        print(f"  - Max locations per cluster: {max_locations_per_cluster}")
        print(f"  - Max boxes per cluster: {max_boxes_per_cluster}")
        print("-" * 60)

        try:
            clusters = clustering_algo.cluster_locations(
                locations=locations,
                num_clusters=num_clusters,
                max_locations_per_cluster=max_locations_per_cluster,
                max_boxes_per_cluster=max_boxes_per_cluster,
                timeout_seconds=30.0,
            )

            # Print results
            print("\nClustering Results:")
            print("=" * 60)

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

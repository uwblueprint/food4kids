#!/usr/bin/env python3
"""
Developer script for visually testing the Sweep algorithm against
real database locations. Fetches locations from the DB, runs clustering, and
saves scatter plots to app/data/.

Run from backend/python/:
    python scripts/sweep_algorithm_test.py

Requires a running database (e.g. via docker compose).
Configure the parameters below before running.

Outputs:
    sweep_clustering_far_deliveries.png — all stops: near vs far (+ warehouse, 35 km ring)
    sweep_clustering_test_exact.png       — exact-N clusters (far stops marked with X)
    sweep_clustering_test.png             — packed clusters (far stops marked with X)
"""

from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, "/app")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.patches import Ellipse
from sqlmodel import Session, create_engine, func, select

from app.models.location import Location
from app.models.route_stop import RouteStop  # noqa: F401
from app.models.system_settings import SystemSettings
from app.services.implementations.sweep_clustering import (
    FAR_DISTANCE_KM_THRESHOLD,
    SweepClusteringAlgorithm,
)

# Use the same connection string as seed_database.py
DATABASE_URL = "postgresql://postgres:postgres@f4k_db:5432/f4k"

# Configure number of locations pulled from csv for testing
LOCATIONS_COUNT = 18

NUM_CLUSTERS = 10
MAX_LOCATIONS_PER_CLUSTER = 5
MAX_BOXES_PER_CLUSTER = 14

OUTPUT_DIR = "./app/data"


def _far_reason_label(algo: SweepClusteringAlgorithm, location: Location) -> str:
    """Human-readable label matching sweep_clustering far detection."""
    metrics = algo._location_metrics(location)
    if not metrics.is_far:
        return "near"
    if algo._is_far_by_address(location):
        return "far (address keyword)"
    return f"far (≥ {FAR_DISTANCE_KM_THRESHOLD:.0f} km)"


def _location_plot_row(
    location: Location,
    *,
    group: int | None,
    far_label: str,
) -> dict[str, object]:
    name = location.school_name or location.contact_name
    is_far = far_label != "near"
    row: dict[str, object] = {
        "name": name,
        "long": location.longitude,
        "lat": location.latitude,
        "is_far": is_far,
        "far_label": far_label,
        "address": location.address,
    }
    if group is not None:
        row["group"] = group
    return row


def _print_far_summary(locations: list[Location], algo: SweepClusteringAlgorithm) -> None:
    print("\nFar delivery classification (same rules as sweep_clustering):")
    print("-" * 60)
    far_count = 0
    for loc in locations:
        label = _far_reason_label(algo, loc)
        name = loc.school_name or loc.contact_name
        metrics = algo._location_metrics(loc)
        if label == "near":
            print(f"  [near] {name} — {metrics.distance_km:.1f} km from warehouse")
        else:
            far_count += 1
            print(f"  [{label}] {name}")
            print(f"         {loc.address}")
            print(f"         {metrics.distance_km:.1f} km from warehouse")
    print(f"\n  Total far: {far_count} / {len(locations)}")
    print("-" * 60)


def _draw_warehouse_and_distance_ring(
    ax: plt.Axes,
    warehouse_lat: float,
    warehouse_lon: float,
) -> None:
    ax.scatter(
        [warehouse_lon],
        [warehouse_lat],
        marker="*",
        s=400,
        c="gold",
        edgecolors="black",
        linewidths=1,
        zorder=10,
        label="Warehouse",
    )
    km_per_deg_lat = 111.0
    km_per_deg_lon = 111.0 * math.cos(math.radians(warehouse_lat))
    width_deg = 2 * FAR_DISTANCE_KM_THRESHOLD / km_per_deg_lon
    height_deg = 2 * FAR_DISTANCE_KM_THRESHOLD / km_per_deg_lat
    ring = Ellipse(
        (warehouse_lon, warehouse_lat),
        width=width_deg,
        height=height_deg,
        fill=False,
        linestyle="--",
        linewidth=1.5,
        edgecolor="dimgray",
        label=f"{FAR_DISTANCE_KM_THRESHOLD:.0f} km from warehouse",
    )
    ax.add_patch(ring)


def _save_far_delivery_plot(
    locations: list[Location],
    algo: SweepClusteringAlgorithm,
    warehouse_lat: float,
    warehouse_lon: float,
) -> None:
    """Standalone map: near vs far stops, warehouse, and haversine threshold ring."""
    rows = [
        _location_plot_row(loc, group=None, far_label=_far_reason_label(algo, loc))
        for loc in locations
    ]
    df = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(11, 9))
    near = df[~df["is_far"]]
    far = df[df["is_far"]]

    if not near.empty:
        ax.scatter(
            near["long"],
            near["lat"],
            c="steelblue",
            s=80,
            alpha=0.85,
            label=f"Near ({len(near)})",
            zorder=3,
        )
    if not far.empty:
        ax.scatter(
            far["long"],
            far["lat"],
            c="crimson",
            s=140,
            marker="X",
            linewidths=1.5,
            edgecolors="darkred",
            label=f"Far ({len(far)})",
            zorder=5,
        )
        for _, row in far.iterrows():
            ax.annotate(
                str(row["far_label"]).replace("far ", ""),
                (row["long"], row["lat"]),
                textcoords="offset points",
                xytext=(6, 6),
                fontsize=7,
                color="darkred",
            )

    _draw_warehouse_and_distance_ring(ax, warehouse_lat, warehouse_lon)
    ax.set_title(
        "Far deliveries (red X) vs near (blue)\n"
        f"Far = address keyword OR ≥ {FAR_DISTANCE_KM_THRESHOLD:.0f} km haversine from warehouse"
    )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(loc="best", fontsize=8)
    ax.set_aspect("equal", adjustable="datalim")

    _write_figure(fig, "sweep_clustering_far_deliveries.png")


def _print_and_collect_rows(
    clusters: list[list[Location]],
    algo: SweepClusteringAlgorithm,
) -> list[dict[str, object]]:
    df_rows: list[dict[str, object]] = []
    for index, cluster in enumerate(clusters):
        print(f"\nCluster {index + 1} ({len(cluster)} locations):")
        print("-" * 40)

        if not cluster:
            print("  (empty cluster)")
            continue

        cluster_boxes = 0
        cluster_has_far = False
        for location in cluster:
            name = location.school_name or location.contact_name
            far_label = _far_reason_label(algo, location)
            if far_label != "near":
                cluster_has_far = True
            print(f"  • {name}" + (" [FAR]" if far_label != "near" else ""))
            print(f"    {location.address}")
            print(f"    Coords: ({location.latitude}, {location.longitude})")
            print(f"    Boxes: {location.num_boxes} | {far_label}")
            cluster_boxes += location.num_boxes
            df_rows.append(
                _location_plot_row(location, group=index, far_label=far_label)
            )

        far_note = " (includes far — max 5 stops/route)" if cluster_has_far else ""
        print(f"\n  Total boxes in cluster: {cluster_boxes}{far_note}")

    return df_rows


def _write_figure(fig: plt.Figure, filename: str) -> None:
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    path = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved plot: {path}")


def _save_cluster_plot(
    df_rows: list[dict[str, object]],
    title: str,
    filename: str,
    warehouse_lat: float,
    warehouse_lon: float,
) -> None:
    if not df_rows:
        return

    df = pd.DataFrame(df_rows)
    fig, ax = plt.subplots(figsize=(11, 9))

    near = df[~df["is_far"]]
    far = df[df["is_far"]]

    if not near.empty:
        sns.scatterplot(
            data=near,
            x="long",
            y="lat",
            hue="group",
            palette="Set2",
            s=70,
            ax=ax,
            legend=True,
        )

    if not far.empty:
        sns.scatterplot(
            data=far,
            x="long",
            y="lat",
            hue="group",
            palette="Set2",
            style="far_label",
            markers=["X"],
            s=200,
            linewidth=2,
            edgecolor="black",
            ax=ax,
            legend=False,
        )

    _draw_warehouse_and_distance_ring(ax, warehouse_lat, warehouse_lon)

    # Custom legend entries for far overlay
    ax.scatter([], [], c="crimson", marker="X", s=120, label="Far delivery stop")
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles=handles, labels=labels, loc="best", fontsize=8)

    ax.set_title(title + "\n(red X = far delivery; dashed ellipse ≈ 35 km from warehouse)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    _write_figure(fig, filename)


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

        clustering_algo = SweepClusteringAlgorithm(
            warehouse_lat=warehouse_lat,
            warehouse_lon=warehouse_lon,
        )

        _print_far_summary(locations, clustering_algo)
        print("\nSaving far-delivery overview plot...")
        _save_far_delivery_plot(
            locations, clustering_algo, warehouse_lat, warehouse_lon
        )

        total_boxes = sum(loc.num_boxes for loc in locations)

        print("\nLocations to cluster:")
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
            rows_exact = _print_and_collect_rows(clusters_exact, clustering_algo)

            _save_cluster_plot(
                rows_exact,
                title=(
                    f"Sweep clustering (exact {NUM_CLUSTERS}) — "
                    f"{len(locations)} locations, {len(clusters_exact)} clusters"
                ),
                filename="sweep_clustering_test_exact.png",
                warehouse_lat=warehouse_lat,
                warehouse_lon=warehouse_lon,
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
            rows_packed = _print_and_collect_rows(clusters_packed, clustering_algo)

            _save_cluster_plot(
                rows_packed,
                title=(
                    f"Sweep clustering (packed) — "
                    f"{len(locations)} locations, {len(clusters_packed)} clusters"
                ),
                filename="sweep_clustering_test.png",
                warehouse_lat=warehouse_lat,
                warehouse_lon=warehouse_lon,
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

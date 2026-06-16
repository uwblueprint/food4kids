#!/usr/bin/env python3
"""
Developer script for visually testing the Sweep algorithm against
real database locations. Fetches locations from the DB, runs clustering, and
saves scatter plots to app/data/.

Run from backend/python/:
    python scripts/sweep_algorithm_test.py

Requires a running database seeded from locations.csv (e.g. seed_database).
Configure the parameters below before running.

Outputs:
    sweep_clustering_far_deliveries.png — all stops: near vs far (+ warehouse, 35 km ring)
    sweep_clustering_test_exact.png       — exact-N clusters (far stops marked with X)
    sweep_clustering_test.png             — packed clusters (far stops marked with X)
"""

from __future__ import annotations

import colorsys
import math
import os
import sys

sys.path.insert(0, "/app")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Ellipse
from sqlmodel import Session, create_engine, select

from app.models.location import Location
from app.models.route_stop import RouteStop  # noqa: F401
from app.models.system_settings import SystemSettings
from app.services.implementations.sweep_clustering import (
    FAR_DISTANCE_KM_THRESHOLD,
    SweepClusteringAlgorithm,
    effective_boxes,
)

# Use the same connection string as seed_database.py
DATABASE_URL = "postgresql://postgres:postgres@f4k_db:5432/f4k"

# Minimum drivers for exact-N mode; actual count scales up with location count.
NUM_CLUSTERS = 10
MAX_LOCATIONS_PER_CLUSTER = 5
MAX_BOXES_PER_CLUSTER = 14
CLUSTER_DETAIL_PRINT_LIMIT = 15

OUTPUT_DIR = "./app/data"


def _num_clusters_for_exact(location_count: int, far_count: int = 0) -> int:
    """Enough drivers for stop/box caps; extra headroom when far routes hit time budget."""
    stop_floor = math.ceil(location_count / MAX_LOCATIONS_PER_CLUSTER)
    # Distant far stops can fill the soft time cap before the 5-stop limit.
    return max(NUM_CLUSTERS, stop_floor + 2 * far_count)


def _unique_hex_palette(count: int) -> list[str]:
    """Return ``count`` visually distinct hex colours with no repeats."""
    if count <= 0:
        return []

    golden_ratio = 0.618033988749895
    palette: list[str] = []
    seen: set[str] = set()

    index = 0
    while len(palette) < count:
        hue = (index * golden_ratio) % 1.0
        saturation = 0.55 + (index % 4) * 0.1
        value = 0.72 + (index % 3) * 0.08
        red, green, blue = colorsys.hsv_to_rgb(
            hue, min(saturation, 0.9), min(value, 0.92)
        )
        hex_color = f"#{int(red * 255):02x}{int(green * 255):02x}{int(blue * 255):02x}"
        if hex_color not in seen:
            seen.add(hex_color)
            palette.append(hex_color)
        index += 1

    return palette


def _group_color_palette(groups: list[object]) -> dict[object, str]:
    """Map each cluster/group id to a unique hex colour."""
    colors = _unique_hex_palette(len(groups))
    return {group: colors[i] for i, group in enumerate(groups)}


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
    name = location.name
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


def _print_far_summary(
    locations: list[Location], algo: SweepClusteringAlgorithm
) -> None:
    print("\nFar delivery classification (same rules as sweep_clustering):")
    print("-" * 60)
    far_count = 0
    for loc in locations:
        label = _far_reason_label(algo, loc)
        name = loc.name
        metrics = algo._location_metrics(loc)
        if label != "near":
            far_count += 1
            print(f"  [{label}] {name}")
            print(f"         {loc.address}")
            print(f"         {metrics.distance_km:.1f} km from warehouse")
    near_count = len(locations) - far_count
    print(f"\n  Total far: {far_count} / {len(locations)}")
    print(f"  Total near: {near_count} (omitted from listing)")
    print("-" * 60)


def _draw_warehouse_and_distance_ring(
    ax: plt.Axes,
    warehouse_lat: float,
    warehouse_lon: float,
) -> None:
    ax.annotate(
        "\u2302",  # Unicode house symbol (⌂)
        xy=(warehouse_lon, warehouse_lat),
        fontsize=24,
        fontweight="bold",
        ha="center",
        va="center",
        color="darkgreen",
        zorder=10,
    )
    # Legend entry (annotate is not picked up automatically).
    ax.plot([], [], linestyle="None", marker="None", label="\u2302 Warehouse")
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
            s=36,
            alpha=0.75,
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
    print_details = len(clusters) <= CLUSTER_DETAIL_PRINT_LIMIT

    for index, cluster in enumerate(clusters):
        cluster_boxes = 0
        cluster_has_far = False
        for location in cluster:
            far_label = _far_reason_label(algo, location)
            if far_label != "near":
                cluster_has_far = True
            cluster_boxes += effective_boxes(location)
            df_rows.append(
                _location_plot_row(location, group=index, far_label=far_label)
            )

        if print_details:
            print(f"\nCluster {index + 1} ({len(cluster)} locations):")
            print("-" * 40)
            if not cluster:
                print("  (empty cluster)")
                continue
            for location in cluster:
                name = location.name
                far_label = _far_reason_label(algo, location)
                print(f"  • {name}" + (" [FAR]" if far_label != "near" else ""))
                print(f"    {location.address}")
                print(f"    Boxes: {effective_boxes(location)} | {far_label}")
            far_note = " (includes far — max 5 stops/route)" if cluster_has_far else ""
            print(f"\n  Total boxes in cluster: {cluster_boxes}{far_note}")

    if not print_details:
        sizes = [len(c) for c in clusters]
        print(
            f"  {len(clusters)} clusters — sizes min={min(sizes)}, "
            f"max={max(sizes)}, avg={sum(sizes) / len(sizes):.1f}"
        )

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

    groups = sorted(df["group"].unique(), key=lambda value: (value is None, value))
    palette = _group_color_palette(list(groups))

    for group in groups:
        subset = df[df["group"] == group]
        color = palette[group]

        near_subset = subset[~subset["is_far"]]
        if not near_subset.empty:
            ax.scatter(
                near_subset["long"],
                near_subset["lat"],
                c=color,
                s=70,
                alpha=0.9,
                edgecolors="white",
                linewidths=0.35,
                zorder=3,
            )

        far_subset = subset[subset["is_far"]]
        if not far_subset.empty:
            ax.scatter(
                far_subset["long"],
                far_subset["lat"],
                c=color,
                marker="X",
                s=200,
                linewidths=2,
                edgecolors="black",
                zorder=5,
            )

    _draw_warehouse_and_distance_ring(ax, warehouse_lat, warehouse_lon)

    ax.scatter([], [], c="crimson", marker="X", s=120, label="Far delivery stop")
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles=handles, labels=labels, loc="best", fontsize=8)

    ax.set_title(
        title + "\n(red X = far delivery; dashed ellipse ≈ 35 km from warehouse)"
    )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    _write_figure(fig, filename)


async def main() -> None:
    engine = create_engine(DATABASE_URL, echo=False)

    with Session(engine) as session:
        statement = select(Location).where(
            Location.latitude != None,  # noqa: E711
            Location.longitude != None,  # noqa: E711
            # 'state' was replaced by the stored roster bit (in_roster);
            # this dev script wants current-roster locations.
            Location.in_roster == True,  # noqa: E712
        )
        locations = list(session.exec(statement).all())
        print(f"Fetched {len(locations)} active locations from database\n")

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

        far_count = sum(
            1 for loc in locations if clustering_algo._location_metrics(loc).is_far
        )
        num_clusters_exact = _num_clusters_for_exact(len(locations), far_count)

        total_boxes = sum(effective_boxes(loc) for loc in locations)

        print(f"Total effective boxes: {total_boxes}")
        print(f"Total locations: {len(locations)}")

        print("\nRunning Sweep clustering (EXACT num_clusters):")
        print(f"  - Number of clusters: {num_clusters_exact}")
        print(f"  - Max locations per cluster: {MAX_LOCATIONS_PER_CLUSTER}")
        print(f"  - Max boxes per cluster: {MAX_BOXES_PER_CLUSTER}")
        print("-" * 60)

        try:
            clusters_exact = await clustering_algo.cluster_locations(
                locations=locations,
                num_clusters=num_clusters_exact,
                max_locations_per_cluster=MAX_LOCATIONS_PER_CLUSTER,
                max_boxes_per_cluster=MAX_BOXES_PER_CLUSTER,
                timeout_seconds=120.0,
            )

            print("\nClustering Results (EXACT num_clusters):")
            print("=" * 60)
            rows_exact = _print_and_collect_rows(clusters_exact, clustering_algo)

            _save_cluster_plot(
                rows_exact,
                title=(
                    f"Sweep clustering (exact {num_clusters_exact}) — "
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
                timeout_seconds=120.0,
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

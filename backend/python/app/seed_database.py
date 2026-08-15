#!/usr/bin/env python3
"""
Comprehensive database seeding script with advanced features.
"""

import argparse
import csv
import os
import random
import uuid
import zlib
from datetime import date, datetime, time, timedelta, timezone
from itertools import pairwise
from typing import cast

import faker
import firebase_admin
import phonenumbers
import polyline
from firebase_admin import auth
from phonenumbers import PhoneNumberFormat
from sklearn.cluster import KMeans  # type: ignore[import-untyped]
from sqlalchemy import create_engine, text
from sqlmodel import Session, select

from app import initialize_firebase
from app.models.admin import Admin
from app.models.announcement import Announcement
from app.models.announcement_last_read import AnnouncementLastRead
from app.models.base import BaseModel
from app.models.driver import Driver
from app.models.enum import NotePermission, ProgressEnum
from app.models.job import Job
from app.models.location import Location
from app.models.location_group import LocationGroup
from app.models.note import Note
from app.models.note_chain import NoteChain
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_snapshot import RouteSnapshot
from app.models.route_stop import RouteStop
from app.models.route_stop_snapshot import RouteStopSnapshot
from app.models.system_settings import (
    EmailReminder,
    SystemSettings,
)

# Import all models to register them with SQLModel
from app.models.user import User
from app.utilities.datetime_utils import from_local_wall_clock, now_utc

# Initialize Faker
fake = faker.Faker()

# Configuration constants
# Average number of stops per route (used to calculate number of clusters)
AVG_STOPS_PER_ROUTE = 7.5
# Maximum number of stops per route (seeded data cap, well below the Google
# Maps directions URL limit of 50 waypoints)
MAX_STOPS_PER_ROUTE = 10
# Number of months in the past to generate route groups for
MONTHS_PAST = 2
# Number of months in the future to generate route groups for
MONTHS_FUTURE = 1

# Probability constants
# Probability that a route will have notes
PROBABILITY_ROUTE_NOTES = 0.1
# Probability that a location will have dietary restrictions
PROBABILITY_DIETARY_RESTRICTIONS = 0.3
# Probability that a location will have a number of children specified
PROBABILITY_NUM_CHILDREN = 0.8
# Probability that a location note chain will have notes
PROBABILITY_LOCATION_CHAIN_NOTES = 0.6
# Probability that a route note chain will have notes
PROBABILITY_ROUTE_CHAIN_NOTES = 0.4
# Probability that a driver note chain will have notes
PROBABILITY_DRIVER_CHAIN_NOTES = 0.5
# Max notes per location chain
MAX_LOCATION_CHAIN_NOTES = 3
# Max notes per route chain
MAX_ROUTE_CHAIN_NOTES = 2
# Max notes per driver chain
MAX_DRIVER_CHAIN_NOTES = 3
# Assignment ratio constants
# Ratio of past routes that should be assigned to drivers (1.0 = 100%)
ASSIGNMENT_RATIO_PAST_ROUTES = 1.0
# Ratio of routes in the next week that should be assigned to drivers
ASSIGNMENT_RATIO_NEXT_WEEK = 0.8
# Ratio of future routes (beyond next week) that should be assigned to drivers
ASSIGNMENT_RATIO_FUTURE_ROUTES = 0.4

# Numeric range constants
# Earth's radius in kilometers (used for haversine distance calculations)
EARTH_RADIUS_KM = 6371
# Random state seed for KMeans clustering (for reproducibility)
KMEANS_RANDOM_STATE = 42
# Number of times KMeans will run with different centroid seeds
KMEANS_N_INIT = 10
# Approximate number of days per month (used for date calculations)
DAYS_PER_MONTH = 30
# Minimum number of drivers to create regardless of route count
MIN_DRIVERS = 5
# Number of admin accounts to seed
NUM_SEED_ADMINS = 2
# Shared password for all seeded Firebase accounts
SEED_PASSWORD = "test123"

# A richer announcement feed, posted by different admins and drivers over the
# past few weeks so the list looks like a real, lived-in noticeboard. Each
# entry is (subject, message, days_ago, author_role) where author_role is one
# of the values in ANNOUNCEMENT_AUTHOR_ROLES. Drivers can post announcements
# too (the create endpoint allows driver-or-admin), so the feed mixes both.
ANNOUNCEMENT_AUTHOR_ROLES = ("admin", "driver")
SAMPLE_ANNOUNCEMENTS: list[tuple[str, str, int, str]] = [
    (
        "Welcome to Food4Kids",
        "Welcome to the Food4Kids delivery platform! Please review your assigned routes and reach out if you have any questions.",
        30,
        "admin",
    ),
    (
        "Schedule Update for March",
        "Please note that delivery schedules have been updated for March. Check your routes for the latest stop assignments.",
        24,
        "admin",
    ),
    (
        "New Cold-Storage Procedure",
        "Starting this week, all perishable items must be kept in the insulated bags until drop-off. Please grab a bag from the warehouse before heading out on your route.",
        19,
        "admin",
    ),
    (
        "Gate Code Change on the East Route",
        "Heads up to anyone covering the east route — the gate code at the Maple Street apartments changed to 4821. The old one stopped working for me on Tuesday.",
        16,
        "driver",
    ),
    (
        "Holiday Notice - Good Friday",
        "There will be no deliveries on Good Friday. All routes scheduled for that day have been moved to the preceding Thursday.",
        12,
        "admin",
    ),
    (
        "Spare Cooler Bags Available",
        "I ended up with a couple of extra insulated bags after my route this week. If anyone is running short, find me at the warehouse Thursday morning and I'll pass them along.",
        9,
        "driver",
    ),
    (
        "Spring Food Drive Kickoff",
        "Our spring food drive starts Monday! We are especially short on shelf-stable proteins and low-sugar snacks. Spread the word with your local networks.",
        5,
        "admin",
    ),
    (
        "Thanks for Covering My Friday Stops",
        "Just wanted to say thank you to whoever picked up my Friday route last week while I was out sick. This crew is the best — really appreciate it.",
        4,
        "driver",
    ),
    (
        "Weather Advisory - Drive Safe",
        "Heavy rain is expected across most routes tomorrow. Take your time, and if conditions feel unsafe, contact your coordinator before continuing. Families can wait — your safety comes first.",
        2,
        "admin",
    ),
]
# Number of days considered as "next week" for assignment strategy
NEXT_WEEK_DAYS = 7
# Maximum number of past route groups to fetch when creating jobs
PAST_ROUTE_GROUPS_LIMIT = 5
# Minimum number of jobs to create
MIN_JOBS = 3
# Maximum number of jobs to create
MAX_JOBS = 5

# Range constants
# Minimum number of children at a location
NUM_CHILDREN_MIN = 1
# Maximum number of children at a location
NUM_CHILDREN_MAX = 4
# Minimum hour of day for job start time (24-hour format)
JOB_START_HOUR_MIN = 8
# Maximum hour of day for job start time (24-hour format)
JOB_START_HOUR_MAX = 16
# Minimum hours after start time for job update time
JOB_UPDATE_HOUR_MIN = 1
# Maximum hours after start time for job update time
JOB_UPDATE_HOUR_MAX = 3
# Minimum hours after update time for job finish time
JOB_FINISH_HOUR_MIN = 1
# Maximum hours after update time for job finish time
JOB_FINISH_HOUR_MAX = 4

# Time constants
# Default route start time (HH:MM:SS format)
ROUTE_START_TIME = "08:00:00"
ROUTE_START_TIME_OF_DAY = time(8, 0, 0)
# Drivers are released in waves rather than all at once, so each route in a
# group starts this many minutes after the previous one.
ROUTE_START_STAGGER_MINUTES = 15

# Location group schedule: group name -> (weekday, alternating slot).
# weekday is Monday=0 .. Sunday=6. Groups sharing a weekday are suffixed
# "A"/"B" and deliver on *alternating* weeks, so any given date materializes
# routes for at most one of them (slot None means "every occurrence of that
# weekday", used for groups with no A/B partner).
LOCATION_GROUP_SCHEDULE = {
    "Schools": (4, None),
    "Tuesday A": (1, "A"),
    "Tuesday B": (1, "B"),
    "Wednesday A": (2, "A"),
    "Wednesday B": (2, "B"),
    "Thursday A": (3, "A"),
    "Thursday B": (3, "B"),
}

# Cities that need specific group assignments (will be randomly assigned)
SMALL_CITIES = ["cambridge", "elmira", "new hamburg"]

# Warehouse location
WAREHOUSE_LAT, WAREHOUSE_LON = 43.402343, -80.464610
WAREHOUSE_ADDRESS = "330 Trillium Drive, Kitchener, ON"


def get_database_url() -> str:
    """Build the database URL from the environment, like migrations/env.py.

    In production, reads DATABASE_URL directly (supports Neon/Supabase/etc.
    with SSL params). In development, builds from individual POSTGRES_* vars.
    """
    if os.environ.get("APP_ENV") == "production":
        return os.environ["DATABASE_URL"]
    return "postgresql://{username}:{password}@{host}:5432/{db}".format(
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ["DB_HOST"],
        db=os.environ["POSTGRES_DB_DEV"],
    )


def set_timestamps(instance: BaseModel) -> None:
    """Set updated_at to match created_at for seed data"""
    if instance.created_at is not None and instance.updated_at is None:
        instance.updated_at = instance.created_at


def ensure_firebase_user(
    uid: str,
    email: str,
    password: str,
    role: str,
    first_name: str,
    last_name: str,
    *,
    reset_password: bool = False,
) -> str:
    """Create or update a Firebase user so it is always loginable.

    An existing user's password is deliberately left alone. Firebase treats a
    password write as a credential change: it moves the account's
    ``tokensValidAfterTime`` to now, which revokes every ID and refresh token
    already issued. Because ``verify_id_token`` is called with
    ``check_revoked=True``, everyone holding one is signed out on their very
    next request.

    Rewriting the password unconditionally therefore made re-seeding sign out
    every open session — including CI's, which seeds the same Firebase project
    that local development uses, so an unrelated merge would log a developer
    out mid-task. The password does not need writing anyway: it is a constant,
    so on the second run it is already the value being written.

    Measured against the real project, only the password does this — writing
    ``display_name`` or custom claims leaves ``tokensValidAfterTime`` untouched.
    The other fields are still written when they differ, which is why this
    reconciles rather than blindly updating.

    :param reset_password: Write the password even when the account exists, for
        the case where it really has drifted. Signs everyone out; that is the
        point, so it has to be asked for.
    """
    full_name = f"{first_name} {last_name}"
    claims = {"role": role, "given_name": first_name, "family_name": last_name}

    try:
        existing = auth.get_user(uid)
    except auth.UserNotFoundError:
        auth.create_user(
            uid=uid,
            email=email,
            password=password,
            email_verified=True,
            display_name=full_name,
        )
        auth.set_custom_user_claims(uid, claims)
        print(f"  Firebase user {uid} ({email}) created")
        return uid

    changes: dict[str, object] = {}
    if existing.email != email:
        changes["email"] = email
    if existing.display_name != full_name:
        changes["display_name"] = full_name
    if not existing.email_verified:
        changes["email_verified"] = True
    if reset_password:
        changes["password"] = password

    if changes:
        auth.update_user(uid, **changes)
    if (existing.custom_claims or {}) != claims:
        auth.set_custom_user_claims(uid, claims)

    updated = ", ".join(sorted(changes)) if changes else "nothing to change"
    print(f"  Firebase user {uid} ({email}) already exists, {updated}")
    return uid


def generate_valid_phone(*, with_extension: bool = False) -> str:
    """Generate a valid phone number in the stored RFC 3966 format.

    ``with_extension`` seeds the ``;ext=`` case — schools and the F4K office
    have extensions, so at least some seeded data should carry one.
    """
    # Valid Canadian area codes (Ontario and Quebec)
    valid_area_codes = [416, 647, 437, 514, 613, 905, 289, 519, 226, 705, 807, 343, 365]

    # Keep trying until we get a valid number
    max_attempts = 100
    for _ in range(max_attempts):
        area_code = random.choice(valid_area_codes)
        exchange = random.randint(200, 999)  # Exchange code (3 digits)
        number = random.randint(1000, 9999)  # Last 4 digits
        phone_str = f"+1{area_code}{exchange:03d}{number:04d}"
        if with_extension:
            phone_str += f" ext. {random.randint(1, 999)}"

        try:
            parsed = phonenumbers.parse(phone_str, None)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, PhoneNumberFormat.RFC3966)
        except Exception:
            continue

    # Fallback: return a known valid number if we can't generate one
    return "tel:+1-416-555-1234"


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate haversine distance between two points in km"""
    from math import asin, cos, radians, sin, sqrt

    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = EARTH_RADIUS_KM
    return c * r


def simple_tsp(
    warehouse_lat: float,
    warehouse_lon: float,
    locations: list[tuple[float, float, str]],
) -> list[str]:
    """Simple greedy TSP starting from warehouse"""
    if not locations:
        return []

    unvisited = locations.copy()
    route = []
    current_lat, current_lon = warehouse_lat, warehouse_lon

    while unvisited:
        # Find nearest unvisited location
        nearest_idx = 0
        nearest_dist = haversine_distance(
            current_lat, current_lon, unvisited[0][0], unvisited[0][1]
        )

        for i, (lat, lon, _) in enumerate(unvisited[1:], 1):
            dist = haversine_distance(current_lat, current_lon, lat, lon)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_idx = i

        # Add to route and update current position
        current_lat, current_lon, location_id = unvisited.pop(nearest_idx)
        route.append(location_id)

    return route


def create_clusters(
    group_locations: list[Location], num_clusters: int
) -> list[list[Location]]:
    """Create clusters from group locations using k-means or simple grouping"""
    if len(group_locations) <= num_clusters:
        return [group_locations]

    # Assert that all locations have coordinates
    for loc in group_locations:
        assert loc.latitude is not None and loc.longitude is not None, (
            f"Location {loc.location_id} is missing coordinates"
        )

    coords = [(loc.latitude, loc.longitude) for loc in group_locations]
    # TODO: Eventually write our own implementation or different algorithm to avoid using scikit-learn
    kmeans = KMeans(
        n_clusters=num_clusters, random_state=KMEANS_RANDOM_STATE, n_init=KMEANS_N_INIT
    )
    cluster_labels = kmeans.fit_predict(coords)

    clusters: list[list[Location]] = [[] for _ in range(num_clusters)]
    for i, location in enumerate(group_locations):
        clusters[cluster_labels[i]].append(location)

    return clusters


def calculate_route_length(
    route_order: list[str],
    cluster_locations: list[Location],
    warehouse_lat: float,
    warehouse_lon: float,
) -> float:
    """Calculate total route length using haversine distance"""
    total_length = 0.0
    prev_lat, prev_lon = warehouse_lat, warehouse_lon

    for location_id in route_order:
        location = next(
            loc for loc in cluster_locations if str(loc.location_id) == location_id
        )
        if location.latitude is None or location.longitude is None:
            continue
        dist = haversine_distance(
            prev_lat, prev_lon, location.latitude, location.longitude
        )
        total_length += dist
        prev_lat, prev_lon = location.latitude, location.longitude

    return total_length


"""Shape of the synthetic path drawn between consecutive stops.

Points per leg buys the bend its resolution; the fraction is how far off the
straight line the middle of a leg is pushed, as a share of that leg's own
length, so the bend stays proportional whether the next stop is 200m or 5km
away.
"""
POLYLINE_POINTS_PER_LEG = 6
POLYLINE_BEND_FRACTION = 0.12


def build_route_polyline(ordered_coords: list[tuple[float, float]], seed: int) -> str:
    """Encode a plausible-looking path through `ordered_coords`.

    This does NOT follow real streets. The seeder has no routing provider, so
    each leg is drawn as a bowed curve between its two stops — enough for the
    route maps to read as routes instead of a star of straight lines out of the
    warehouse, and nothing more. In production `encoded_polyline` comes from the
    routing provider, so no code should ever treat a seeded polyline as
    directions or measure anything off it; `Route.length` remains the haversine
    figure the rest of the seeder already computes.

    `seed` keeps a given cluster's shape stable across seed runs. The draws go
    through a local Random rather than the module-level one on purpose: pulling
    from the global stream here would shift every downstream random choice in
    the seeder and silently change unrelated fixture data.
    """
    if len(ordered_coords) < 2:
        return ""

    rng = random.Random(seed)
    path: list[tuple[float, float]] = [ordered_coords[0]]

    for (lat1, lon1), (lat2, lon2) in pairwise(ordered_coords):
        dlat, dlon = lat2 - lat1, lon2 - lon1
        # Perpendicular to the leg, so the offset bows the segment sideways
        # rather than stretching it past either stop.
        perp_lat, perp_lon = -dlon, dlat
        bend = rng.uniform(-POLYLINE_BEND_FRACTION, POLYLINE_BEND_FRACTION)

        for step in range(1, POLYLINE_POINTS_PER_LEG):
            t = step / POLYLINE_POINTS_PER_LEG
            # Zero at t=0 and t=1, widest mid-leg: the curve always meets its
            # stops exactly, so markers sit on the line instead of beside it.
            arc = bend * (4.0 * t * (1.0 - t))
            path.append(
                (lat1 + dlat * t + perp_lat * arc, lon1 + dlon * t + perp_lon * arc)
            )
        path.append((lat2, lon2))

    # precision=5 is the Google encoding the routing provider returns, and what
    # the frontend's decoder assumes.
    return polyline.encode(path, precision=5)


class ClusterPlan:
    """Pre-computed TSP plan for one cluster within one location group.

    We cluster + TSP once per location_group, then materialize a per-day
    Route instance from this plan for every matching drive_date. Cheaper
    than re-clustering for every RouteGroup, and the deterministic
    KMeans seed means we get the same plan each seed run.
    """

    def __init__(
        self,
        cluster_idx: int,
        ordered_location_ids: list[str],
        cluster_locations: list[Location],
        length_km: float,
        encoded_polyline: str,
    ):
        self.cluster_idx = cluster_idx
        self.ordered_location_ids = ordered_location_ids
        self.cluster_locations = cluster_locations
        self.length_km = length_km
        # Computed with the plan, not per Route: every drive_date materialized
        # from this cluster drives the same stops in the same order.
        self.encoded_polyline = encoded_polyline


def plan_clusters_for_group(
    group_locations: list[Location],
) -> list[ClusterPlan]:
    """Cluster a location_group's locations + greedily TSP each cluster.

    Returns one ClusterPlan per cluster. Empty input → empty list. We
    intentionally skip groups with <2 locations (matches old behaviour).
    """
    if len(group_locations) < 2:
        return []

    num_clusters = max(1, int(len(group_locations) // AVG_STOPS_PER_ROUTE))
    clusters = create_clusters(group_locations, num_clusters)

    # Split any cluster that exceeds the max stops per route
    split_clusters: list[list[Location]] = []
    for cluster in clusters:
        while len(cluster) > MAX_STOPS_PER_ROUTE:
            split_clusters.append(cluster[:MAX_STOPS_PER_ROUTE])
            cluster = cluster[MAX_STOPS_PER_ROUTE:]
        if cluster:
            split_clusters.append(cluster)
    clusters = split_clusters

    plans: list[ClusterPlan] = []
    for cluster_idx, cluster_locations in enumerate(clusters):
        if not cluster_locations:
            continue

        for loc in cluster_locations:
            assert loc.latitude is not None and loc.longitude is not None, (
                f"Location {loc.location_id} is missing coordinates"
            )

        tsp_locations = cast(
            "list[tuple[float, float, str]]",
            [
                (loc.latitude, loc.longitude, str(loc.location_id))
                for loc in cluster_locations
            ],
        )
        route_order = simple_tsp(WAREHOUSE_LAT, WAREHOUSE_LON, tsp_locations)
        total_length = calculate_route_length(
            route_order, cluster_locations, WAREHOUSE_LAT, WAREHOUSE_LON
        )

        # Routes leave the warehouse and finish at their last stop
        # (ends_at_warehouse is False for seeded routes), matching the legs
        # calculate_route_length already measures.
        by_id = {str(loc.location_id): loc for loc in cluster_locations}
        coords: list[tuple[float, float]] = [(WAREHOUSE_LAT, WAREHOUSE_LON)]
        for location_id in route_order:
            location = by_id[location_id]
            coords.append(
                (cast("float", location.latitude), cast("float", location.longitude))
            )

        plans.append(
            ClusterPlan(
                cluster_idx=cluster_idx,
                ordered_location_ids=route_order,
                cluster_locations=cluster_locations,
                length_km=round(total_length, 2),
                # crc32 over the stop order, not hash(): hash() is salted per
                # process, which would reshape every route on each seed run.
                encoded_polyline=build_route_polyline(
                    coords, zlib.crc32("".join(route_order).encode())
                ),
            )
        )
    return plans


def pick_assignment_ratio(drive_date: date, today: date) -> float:
    """Date-bucketed driver-assignment density (mirrors old DriverAssignment seed)."""
    if drive_date < today:
        return ASSIGNMENT_RATIO_PAST_ROUTES
    if drive_date <= today + timedelta(days=NEXT_WEEK_DAYS):
        return ASSIGNMENT_RATIO_NEXT_WEEK
    return ASSIGNMENT_RATIO_FUTURE_ROUTES


def materialize_route_for_group(
    session: Session,
    route_group: RouteGroup,
    plan: ClusterPlan,
    *,
    drive_date: date,
    today: date,
    driver_ids: list[uuid.UUID],
) -> Route:
    """Create one Route (and its stops) inside the given RouteGroup.

    Past routes additionally get a RouteSnapshot + RouteStopSnapshot per
    stop, mirroring what the nightly cron would have produced.
    """
    assign_ratio = pick_assignment_ratio(drive_date, today)
    driver_id: uuid.UUID | None = (
        random.choice(driver_ids)
        if driver_ids and random.random() < assign_ratio
        else None
    )

    # An assigned route must carry a start time (enforced by a CHECK
    # constraint). Drivers leave in waves, so stagger each route in the group
    # off the standard start; an unassigned route stays unscheduled.
    start_time: time | None = None
    if driver_id is not None:
        start_time = (
            datetime.combine(date.min, ROUTE_START_TIME_OF_DAY)
            + timedelta(minutes=ROUTE_START_STAGGER_MINUTES * plan.cluster_idx)
        ).time()

    route = Route(
        name=f"Route {plan.cluster_idx + 1}",
        notes=fake.sentence() if random.random() < PROBABILITY_ROUTE_NOTES else "",
        length=plan.length_km,
        route_group_id=route_group.route_group_id,
        driver_id=driver_id,
        start_time=start_time,
        encoded_polyline=plan.encoded_polyline or None,
        polyline_updated_at=(
            datetime.now(timezone.utc) if plan.encoded_polyline else None
        ),
    )
    set_timestamps(route)
    session.add(route)
    session.flush()  # need route_id for stops

    created_stops: list[RouteStop] = []
    for stop_num, location_id in enumerate(plan.ordered_location_ids, start=1):
        stop = RouteStop(
            route_id=route.route_id,
            location_id=uuid.UUID(location_id),
            stop_number=stop_num,
        )
        set_timestamps(stop)
        session.add(stop)
        created_stops.append(stop)
    session.flush()  # need route_stop_ids for snapshots

    # Freeze past routes so historical reads work without first running the cron.
    if drive_date < today:
        route_snap = RouteSnapshot(
            route_id=route.route_id,
            start_address=WAREHOUSE_ADDRESS,
            start_latitude=WAREHOUSE_LAT,
            start_longitude=WAREHOUSE_LON,
        )
        set_timestamps(route_snap)
        session.add(route_snap)

        loc_by_id = {str(loc.location_id): loc for loc in plan.cluster_locations}
        for stop in created_stops:
            loc = loc_by_id[str(stop.location_id)]
            if loc.latitude is None or loc.longitude is None:
                continue
            stop_snap = RouteStopSnapshot(
                route_stop_id=stop.route_stop_id,
                address=loc.address,
                contact_name=loc.contact_name,
                phone_primary=loc.phone_primary,
                phone_secondary=loc.phone_secondary,
                num_children=loc.num_children,
                latitude=loc.latitude,
                longitude=loc.longitude,
            )
            set_timestamps(stop_snap)
            session.add(stop_snap)

    return route


def main(*, reset_passwords: bool = False) -> None:
    """Main seeding function

    :param reset_passwords: Rewrite every seeded account's password to
        ``SEED_PASSWORD``, signing out everyone currently holding a token. Off
        by default so a routine re-seed leaves open sessions alone; see
        ``ensure_firebase_user``.
    """
    print("Starting final database seeding...")

    if not firebase_admin._apps:  # type: ignore[attr-defined]
        initialize_firebase()
    print("Firebase initialized")

    # Create database connection
    engine = create_engine(get_database_url(), echo=False)

    with Session(engine) as session:
        try:
            # Clear existing data. Order matters: snapshots & stops first
            # (FK to routes), then routes (FK to route_groups), then
            # route_groups.
            print("Clearing existing data...")
            tables_to_clear = [
                "announcement_last_reads",
                "notes",
                "jobs",
                "route_stop_snapshots",
                "route_snapshots",
                "route_stops",
                "routes",
                "route_groups",
                "locations",
                "location_groups",
                "drivers",
                "admin_info",
                "note_chains",
                "system_settings",
                "users",
            ]

            for table in tables_to_clear:
                try:
                    session.execute(text(f"DELETE FROM {table}"))
                except Exception as e:
                    print(f"Warning: Could not clear {table}: {e}")

            session.commit()
            print("Database cleared successfully")

            # Create admin accounts first so every note chain below can be
            # authored by a real admin.
            print("Creating admin accounts...")
            admin_users: list[User] = []

            for i in range(NUM_SEED_ADMINS):
                admin_num = i + 1
                uid = f"seed-admin-{admin_num}"
                email = f"admin{admin_num}@f4k.dev"
                first_name = fake.first_name()
                last_name = fake.last_name()

                ensure_firebase_user(
                    uid=uid,
                    email=email,
                    password=SEED_PASSWORD,
                    role="admin",
                    first_name=first_name,
                    last_name=last_name,
                    reset_password=reset_passwords,
                )

                user = User(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    auth_id=uid,
                    role="admin",
                )
                set_timestamps(user)
                session.add(user)

                admin = Admin(
                    admin_phone=generate_valid_phone(),
                    user_id=user.user_id,
                )
                set_timestamps(admin)
                session.add(admin)

                admin_users.append(user)

            session.commit()
            print(f"Created {NUM_SEED_ADMINS} admin accounts")
            # Author pool for the notes seeded into note chains below.
            admin_author_ids = [user.user_id for user in admin_users]

            # Create location groups
            print("Creating location groups...")
            group_names = list(LOCATION_GROUP_SCHEDULE.keys())
            group_ids: dict[str, str] = {}
            for name in group_names:
                location_group = LocationGroup(
                    name=name,
                    color=fake.hex_color(),
                    notes="",
                )
                set_timestamps(location_group)
                session.add(location_group)
                group_ids[name] = str(location_group.location_group_id)

            session.commit()
            print(f"Created {len(group_names)} location groups")

            # Create locations from CSV
            print("Creating locations from CSV...")
            # Allow CSV path to be overridden via environment variable for testing
            csv_path = os.getenv("LOCATIONS_CSV_PATH", "app/data/locations.csv")
            locations_created = 0

            non_school_groups = [
                gid for name, gid in group_ids.items() if name != "Schools"
            ]
            schools_group_id = group_ids.get("Schools")

            if os.path.exists(csv_path):
                with open(csv_path) as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        address = row.get("formatted_address", "")
                        lat, lon = (
                            float(row.get("latitude", 0)),
                            float(row.get("longitude", 0)),
                        )

                        # Determine location group. Every location must
                        # belong to a delivery group (FK is non-nullable).
                        is_small_city = any(
                            city in address.lower() for city in SMALL_CITIES
                        )
                        if is_small_city:
                            # Random assignment from non-school groups for small cities
                            group_id = random.choice(non_school_groups)
                        else:
                            group_id = random.choice(list(group_ids.values()))

                        # delivery_type follows the assigned group: anything
                        # in the "Schools" group is a School recipient,
                        # everything else is a Family. Matches the per-group
                        # uniform invariant we'll later enforce at generation.
                        is_school = (
                            schools_group_id is not None
                            and group_id == schools_group_id
                        )
                        delivery_type = "School" if is_school else "Family"

                        contact_name = fake.name()
                        location = Location(
                            location_group_id=uuid.UUID(group_id),
                            name=f"{fake.company()} School"
                            if is_school
                            else contact_name,
                            contact_name=contact_name,
                            address=address,
                            # Schools answer on a switchboard — seed them with
                            # extensions so the ;ext= path is exercised.
                            phone_primary=generate_valid_phone(
                                with_extension=is_school
                            ),
                            phone_secondary=generate_valid_phone()
                            if random.choice([True, False])
                            else None,
                            longitude=lon,
                            latitude=lat,
                            halal=random.choice([True, False]),
                            dietary_restrictions=fake.sentence()
                            if random.random() < PROBABILITY_DIETARY_RESTRICTIONS
                            else "",
                            # num_children is required; box count is derived from
                            # it. Seed a 0 sometimes to exercise the zero-box case.
                            num_children=random.randint(
                                NUM_CHILDREN_MIN, NUM_CHILDREN_MAX
                            )
                            if random.random() < PROBABILITY_NUM_CHILDREN
                            else 0,
                            delivery_type=delivery_type,
                            in_roster=True,
                        )
                        set_timestamps(location)
                        session.add(location)
                        locations_created += 1
            else:
                raise FileNotFoundError(f"Locations CSV file not found at {csv_path}")

            session.commit()
            print(f"Created {locations_created} locations")

            # Cluster + TSP per location group (once each). We materialize
            # the actual Route rows per drive_date in the loop below.
            print("Planning route clusters per location group...")
            all_locations = list(session.exec(select(Location)).all())
            locations_by_group: dict[str, list[Location]] = {}
            for loc in all_locations:
                gid = str(loc.location_group_id)
                locations_by_group.setdefault(gid, []).append(loc)

            cluster_plans_by_group: dict[str, list[ClusterPlan]] = {
                gid: plan_clusters_for_group(locs)
                for gid, locs in locations_by_group.items()
            }
            total_clusters = sum(
                len(plans) for plans in cluster_plans_by_group.values()
            )
            print(f"Planned {total_clusters} route templates across location groups")

            # Drivers must exist before we materialize routes (because we
            # assign Route.driver_id during creation now).
            print("Creating drivers...")
            # Per-day route instances are materialized later from the cluster
            # plans, so size the driver pool off total_clusters (routes don't
            # exist yet at this point in the refactored ordering).
            num_drivers = max(total_clusters, MIN_DRIVERS)

            for i in range(num_drivers):
                n = f"{i + 1:03d}"
                uid = f"seed-driver-{n}"
                email = f"driver{n}@f4k.dev"
                first_name = fake.first_name()
                last_name = fake.last_name()

                ensure_firebase_user(
                    uid=uid,
                    email=email,
                    password=SEED_PASSWORD,
                    role="driver",
                    first_name=first_name,
                    last_name=last_name,
                    reset_password=reset_passwords,
                )

                user = User(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    auth_id=uid,
                    role="driver",
                )
                set_timestamps(user)
                session.add(user)

                # Ensure at least the first half of drivers are active
                is_active = (
                    True if i < num_drivers // 2 else random.choice([True, False])
                )

                # Every driver owns an admin-only note chain (read AND write =
                # Admin) so admins can leave notes the driver can't see — mirrors
                # DriverService.create_driver.
                note_chain = NoteChain(
                    read_permission=NotePermission.ADMIN,
                    write_permission=NotePermission.ADMIN,
                )
                set_timestamps(note_chain)
                session.add(note_chain)
                session.flush()

                driver = Driver(
                    user_id=user.user_id,
                    phone=generate_valid_phone(),
                    partner_driver_name=fake.name()
                    if random.choice([True, False])
                    else None,
                    availability=[random.choice([True, False]) for _ in range(7)],
                    address=fake.address(),
                    license_plate=fake.license_plate(),
                    car_make_model=fake.word().title() + " " + fake.word().title(),
                    active=is_active,
                    note_chain_id=note_chain.note_chain_id,
                )
                set_timestamps(driver)
                session.add(driver)

                # Seed admin-authored notes into the driver's admin-only chain.
                if random.random() < PROBABILITY_DRIVER_CHAIN_NOTES:
                    for _ in range(random.randint(1, MAX_DRIVER_CHAIN_NOTES)):
                        note = Note(
                            note_chain_id=note_chain.note_chain_id,
                            user_id=random.choice(admin_author_ids),
                            message=fake.sentence(),
                            is_system=False,
                        )
                        set_timestamps(note)
                        session.add(note)
            session.commit()
            print(f"Created {num_drivers} drivers")

            # Active driver pool used for per-route assignment.
            active_driver_rows = session.execute(
                text("SELECT driver_id FROM drivers WHERE active = TRUE")
            ).fetchall()
            active_driver_ids: list[uuid.UUID] = [row[0] for row in active_driver_rows]
            if not active_driver_ids:
                print("Warning: No active drivers; all routes will be unassigned.")

            # Create route groups + per-day route instances together.
            print("Creating route groups + per-day route instances...")
            route_groups_created = 0
            routes_created = 0
            today = datetime.now().date()
            start_date = today - timedelta(days=MONTHS_PAST * DAYS_PER_MONTH)
            end_date = today + timedelta(days=MONTHS_FUTURE * DAYS_PER_MONTH)

            current_date = start_date
            while current_date <= end_date:
                weekday = current_date.weekday()
                # Continuous week index (never resets across years), so
                # consecutive occurrences of the same weekday always flip the
                # slot -> A and B groups alternate week to week.
                week_slot = "A" if (current_date.toordinal() // 7) % 2 == 0 else "B"
                matching_groups = [
                    name
                    for name, (target_weekday, slot) in LOCATION_GROUP_SCHEDULE.items()
                    if target_weekday == weekday and (slot is None or slot == week_slot)
                ]

                for group_name in matching_groups:
                    loc_group_id = group_ids.get(group_name)
                    if not loc_group_id:
                        continue
                    plans = cluster_plans_by_group.get(loc_group_id, [])
                    if not plans:
                        continue

                    route_group = RouteGroup(
                        name=f"{group_name} - {current_date.strftime('%Y-%m-%d')}",
                        notes=f"Route group for {group_name} on {current_date}",
                        drive_date=current_date,
                    )
                    set_timestamps(route_group)
                    session.add(route_group)
                    session.flush()  # need route_group_id

                    for plan in plans:
                        materialize_route_for_group(
                            session,
                            route_group,
                            plan,
                            drive_date=current_date,
                            today=today,
                            driver_ids=active_driver_ids,
                        )
                        routes_created += 1
                    route_groups_created += 1

                current_date += timedelta(days=1)

            session.commit()
            print(
                f"Created {route_groups_created} route groups "
                f"and {routes_created} route instances"
            )

            # ----------------------------------------------------------------
            # Explicit test fixtures. Dated one day before every other seeded
            # group so they pin to the top of the oldest-first routes feed (page
            # size 50), where the random past data is otherwise all assigned and
            # fully stopped. These exercise UI states the random data won't
            # reliably surface on page 1:
            #   - two unassigned routes -> the "missing assigned drivers" banner
            #   - a route with no stops -> route delete enabled
            #   - a route with stops   -> route delete disabled (tooltip)
            #   - an empty route group -> group delete enabled
            #   - unscheduled + inactive standalone locations -> status/filter,
            #     both safe to delete (not referenced by any route)
            # All are named "TEST ..." so they're easy to spot and remove.
            # ----------------------------------------------------------------
            print("Creating explicit test fixtures...")
            fixture_date = start_date - timedelta(days=1)
            fixture_loc_group_id = group_ids["Tuesday A"]
            # Reuse a few existing locations as stops for the populated route.
            stop_locations = list(
                session.exec(
                    select(Location)
                    .where(
                        Location.location_group_id == uuid.UUID(fixture_loc_group_id)
                    )
                    .limit(3)
                ).all()
            )

            # 1) Empty group: no routes -> Groups tab delete enabled.
            empty_group = RouteGroup(
                name="TEST - Empty Group (no routes)",
                notes="Seeded fixture: empty group, safe to delete.",
                drive_date=fixture_date,
            )
            set_timestamps(empty_group)
            session.add(empty_group)

            # 2) Group with two unassigned routes: one with no stops (route
            #    delete enabled) and one with stops (route delete disabled ->
            #    tooltip). Both unassigned -> Routes banner reads "2 routes ...".
            fixture_group = RouteGroup(
                name="TEST - Fixture Routes",
                notes="Seeded fixture: unassigned routes for banner/delete tests.",
                drive_date=fixture_date,
            )
            set_timestamps(fixture_group)
            session.add(fixture_group)
            session.flush()

            route_no_stops = Route(
                name="TEST Route (no stops)",
                notes="Seeded fixture: no stops, delete enabled.",
                length=0.0,
                route_group_id=fixture_group.route_group_id,
                driver_id=None,
            )
            set_timestamps(route_no_stops)
            session.add(route_no_stops)

            fixture_coords: list[tuple[float, float]] = [
                (WAREHOUSE_LAT, WAREHOUSE_LON),
                *(
                    (loc.latitude, loc.longitude)
                    for loc in stop_locations
                    if loc.latitude is not None and loc.longitude is not None
                ),
            ]
            fixture_polyline = build_route_polyline(
                fixture_coords,
                zlib.crc32(
                    "".join(str(loc.location_id) for loc in stop_locations).encode()
                ),
            )

            route_with_stops = Route(
                name="TEST Route (has stops)",
                notes="Seeded fixture: unassigned, has stops (delete disabled).",
                length=5.0,
                route_group_id=fixture_group.route_group_id,
                driver_id=None,
                encoded_polyline=fixture_polyline or None,
                polyline_updated_at=(
                    datetime.now(timezone.utc) if fixture_polyline else None
                ),
            )
            set_timestamps(route_with_stops)
            session.add(route_with_stops)
            session.flush()

            for stop_num, loc in enumerate(stop_locations, start=1):
                stop = RouteStop(
                    route_id=route_with_stops.route_id,
                    location_id=loc.location_id,
                    stop_number=stop_num,
                )
                set_timestamps(stop)
                session.add(stop)

            # 3) Standalone locations for the Addresses tab: one unscheduled (on
            #    the roster, no upcoming route) and one inactive (off the
            #    roster). Neither is on a route, so both are safe to delete.
            unscheduled_loc = Location(
                location_group_id=uuid.UUID(fixture_loc_group_id),
                name="TEST Unscheduled Family",
                contact_name="TEST Unscheduled Family",
                address="1 Test Street, Kitchener, ON, N2A 0T0",
                phone_primary=generate_valid_phone(),
                longitude=WAREHOUSE_LON,
                latitude=WAREHOUSE_LAT,
                halal=False,
                dietary_restrictions="Nut allergy",
                num_children=2,
                delivery_type="Family",
                in_roster=True,
            )
            inactive_loc = Location(
                location_group_id=uuid.UUID(fixture_loc_group_id),
                name="TEST Inactive Family",
                contact_name="TEST Inactive Family",
                address="2 Test Street, Kitchener, ON, N2A 0T0",
                phone_primary=generate_valid_phone(),
                longitude=WAREHOUSE_LON,
                latitude=WAREHOUSE_LAT,
                halal=True,
                dietary_restrictions="",
                num_children=0,
                delivery_type="Family",
                in_roster=False,
            )
            set_timestamps(unscheduled_loc)
            set_timestamps(inactive_loc)
            session.add(unscheduled_loc)
            session.add(inactive_loc)

            session.commit()
            print(
                "Created test fixtures: 1 empty group, 1 group with 2 unassigned "
                "routes (no-stops + has-stops), 2 standalone locations"
            )

            # Create note chains for locations
            print("Creating note chains for locations...")
            location_chains_created = 0
            location_notes_created = 0
            all_locations = list(session.exec(select(Location)).all())

            for location in all_locations:
                note_chain = NoteChain(
                    read_permission=NotePermission.ALL,
                    write_permission=NotePermission.ALL,
                )
                set_timestamps(note_chain)
                session.add(note_chain)
                session.flush()

                location.note_chain_id = note_chain.note_chain_id
                location_chains_created += 1

                if random.random() < PROBABILITY_LOCATION_CHAIN_NOTES:
                    num_notes = random.randint(1, MAX_LOCATION_CHAIN_NOTES)
                    for _ in range(num_notes):
                        note = Note(
                            note_chain_id=note_chain.note_chain_id,
                            user_id=random.choice(admin_author_ids),
                            message=fake.sentence(),
                            is_system=False,
                        )
                        set_timestamps(note)
                        session.add(note)
                        location_notes_created += 1

            session.commit()
            print(
                f"Created {location_chains_created} location note chains "
                f"with {location_notes_created} notes"
            )

            # Create note chains for routes (only a sample, since the per-day
            # explosion means we'd otherwise generate one per Route instance
            # which is wasteful for seed data).
            print("Creating note chains for routes (sampled)...")
            route_chains_created = 0
            route_notes_created = 0
            all_routes = list(session.exec(select(Route)).all())

            for route in all_routes:
                # Sample so we don't blow up note_chain count; the production
                # signal isn't 1-route-1-chain anyway.
                if random.random() > 0.2:
                    continue
                note_chain = NoteChain(
                    read_permission=NotePermission.ADMIN,
                    write_permission=NotePermission.ADMIN,
                )
                set_timestamps(note_chain)
                session.add(note_chain)
                session.flush()

                route.note_chain_id = note_chain.note_chain_id
                route_chains_created += 1

                if random.random() < PROBABILITY_ROUTE_CHAIN_NOTES:
                    num_notes = random.randint(1, MAX_ROUTE_CHAIN_NOTES)
                    for _ in range(num_notes):
                        note = Note(
                            note_chain_id=note_chain.note_chain_id,
                            user_id=random.choice(admin_author_ids),
                            message=fake.sentence(),
                            is_system=False,
                        )
                        set_timestamps(note)
                        session.add(note)
                        route_notes_created += 1

            session.commit()
            print(
                f"Created {route_chains_created} route note chains "
                f"with {route_notes_created} notes"
            )

            # Create jobs (linked to past route groups)
            print("Creating jobs...")
            past_route_groups = session.execute(
                text(
                    """
                    SELECT route_group_id, drive_date
                    FROM route_groups
                    WHERE drive_date < CURRENT_DATE
                    ORDER BY drive_date DESC
                    LIMIT :limit
                    """
                ),
                {"limit": PAST_ROUTE_GROUPS_LIMIT},
            ).fetchall()

            jobs_created = 0
            if past_route_groups:
                available = len(past_route_groups)
                num_jobs = random.randint(
                    min(MIN_JOBS, available), min(MAX_JOBS, available)
                )
                selected_groups = random.sample(past_route_groups, num_jobs)
                jobs_created = len(selected_groups)

                for route_group_id, drive_date in selected_groups:
                    # The hour is a wall-clock hour on the drive date, so read it
                    # in the app's timezone rather than handing Postgres a naive
                    # value it would resolve against the session timezone.
                    started_at = from_local_wall_clock(
                        datetime.combine(
                            drive_date,
                            time(
                                hour=random.randint(
                                    JOB_START_HOUR_MIN, JOB_START_HOUR_MAX
                                )
                            ),
                        )
                    )
                    updated_at = started_at + timedelta(
                        hours=random.randint(JOB_UPDATE_HOUR_MIN, JOB_UPDATE_HOUR_MAX)
                    )
                    finished_at = updated_at + timedelta(
                        hours=random.randint(JOB_FINISH_HOUR_MIN, JOB_FINISH_HOUR_MAX)
                    )

                    job = Job(
                        route_group_id=route_group_id,
                        progress=ProgressEnum.COMPLETED,
                        started_at=started_at,
                        updated_at=updated_at,
                        finished_at=finished_at,
                    )
                    set_timestamps(job)
                    session.add(job)

            session.commit()
            print(f"Created {jobs_created} jobs")

            # Create system settings
            print("Creating system settings info...")
            route_start_time_obj = datetime.strptime(
                ROUTE_START_TIME, "%H:%M:%S"
            ).time()
            system_settings = SystemSettings(
                route_start_time=route_start_time_obj,
                warehouse_location=WAREHOUSE_ADDRESS,
                warehouse_longitude=WAREHOUSE_LON,
                warehouse_latitude=WAREHOUSE_LAT,
                boxes_per_car=10,
                dropoff_minutes=3,
                children_per_box=2,
                contact_name="Emily Loro",
                # The real office number has an extension; keep the seed honest.
                contact_phone=generate_valid_phone(with_extension=True),
                f4k_wr_instagram="https://instagram.com/food4kidswr",
                f4k_wr_facebook="https://facebook.com/food4kidswr",
                f4k_wr_email="hello@food4kidswr.ca",
                f4k_wr_website="https://food4kidswr.ca",
                f4k_wr_address=WAREHOUSE_ADDRESS,
                email_reminders=[
                    EmailReminder(days_before=1, time=time(9, 0, 0)),
                    EmailReminder(days_before=0, time=time(11, 0, 0)),
                ],
            )
            set_timestamps(system_settings)
            session.add(system_settings)

            session.commit()
            print("Created system settings info")

            # Create sample announcements
            print("Creating sample announcements...")
            # Drivers can post announcements too (the create endpoint allows
            # driver-or-admin), so pull a pool of driver users to author some of
            # the feed alongside the admins.
            driver_user_ids: list[uuid.UUID] = [
                row[0]
                for row in session.execute(
                    text("SELECT user_id FROM users WHERE role = 'driver'")
                ).fetchall()
            ]
            admin_user_ids: list[uuid.UUID] = [user.user_id for user in admin_users]

            # Rotate authorship within each role so the feed shows messages from
            # more than one person rather than a single author.
            role_counts = dict.fromkeys(ANNOUNCEMENT_AUTHOR_ROLES, 0)
            for subject, message, days_ago, author_role in SAMPLE_ANNOUNCEMENTS:
                if author_role == "admin":
                    pool = admin_user_ids
                elif author_role == "driver":
                    pool = driver_user_ids
                else:
                    raise ValueError(f"Unknown announcement author role: {author_role}")

                author_user_id = pool[role_counts[author_role] % len(pool)]
                role_counts[author_role] += 1

                announcement = Announcement(
                    subject=subject,
                    message=message,
                    user_id=author_user_id,
                    attachments=[],
                )
                set_timestamps(announcement)
                posted_at = now_utc() - timedelta(days=days_ago)
                announcement.created_at = posted_at
                announcement.updated_at = posted_at
                session.add(announcement)
            session.commit()
            print(f"Created {len(SAMPLE_ANNOUNCEMENTS)} sample announcements")

            # Create announcement read tracking entries for some drivers
            print("Creating announcement read tracking entries...")
            read_entries_created = 0
            all_driver_users = session.execute(
                text(
                    "SELECT u.user_id FROM users u JOIN drivers d ON u.user_id = d.user_id"
                )
            ).fetchall()

            for driver_user_row in all_driver_users:
                if random.random() < 0.6:
                    read_entry = AnnouncementLastRead(
                        user_id=driver_user_row[0],
                        last_read_at=now_utc() - timedelta(hours=random.randint(0, 72)),
                    )
                    set_timestamps(read_entry)
                    session.add(read_entry)
                    read_entries_created += 1

            session.commit()
            print(f"Created {read_entries_created} announcement read tracking entries")

            print("Comprehensive database seeding completed successfully!")

            print("\n=== Seed Account Credentials ===")
            print(f"Password for all accounts: {SEED_PASSWORD}")
            print(f"Drivers: driver001@f4k.dev ... driver{num_drivers:03d}@f4k.dev")
            print(f"Admins:  admin1@f4k.dev ... admin{NUM_SEED_ADMINS}@f4k.dev")
            print("================================\n")

        except Exception as e:
            print(f"Error during seeding: {e}")
            session.rollback()
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset-passwords",
        action="store_true",
        help=(
            f"Rewrite every seeded account's password to '{SEED_PASSWORD}'. "
            "Signs out everyone currently logged in, so it is off by default — "
            "use it only when a password has actually drifted."
        ),
    )
    main(reset_passwords=parser.parse_args().reset_passwords)

#!/usr/bin/env python3
"""
Comprehensive database seeding script with advanced features.
"""

import csv
import os
import random
import uuid
from datetime import date, datetime, time, timedelta
from typing import cast
from zoneinfo import ZoneInfo

import faker
import firebase_admin
import phonenumbers
from firebase_admin import auth
from phonenumbers import PhoneNumberFormat
from sklearn.cluster import KMeans  # type: ignore[import-untyped]
from sqlalchemy import create_engine, text
from sqlmodel import Session, select

from app import initialize_firebase
from app.models.admin import Admin
from app.models.announcement import Announcement
from app.models.base import BaseModel
from app.models.driver import Driver
from app.models.driver_history import DriverHistory
from app.models.enum import DeliveryTypeEnum, NotePermission, ProgressEnum
from app.models.job import Job
from app.models.location import Location
from app.models.location_group import LocationGroup
from app.models.note import Note
from app.models.note_chain import NoteChain
from app.models.note_chain_read import NoteChainReadModel
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_snapshot import RouteSnapshot
from app.models.route_stop import RouteStop
from app.models.route_stop_snapshot import RouteStopSnapshot
from app.models.system_settings import EmailReminder, SystemSettings

# Import all models to register them with SQLModel
from app.models.user import User

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
# Probability that a location will have notes
PROBABILITY_LOCATION_NOTES = 0.4
# Probability to skip creating driver history for the current year
PROBABILITY_SKIP_CURRENT_YEAR_HISTORY = 0.2
# Probability that a location note chain will have notes
PROBABILITY_LOCATION_CHAIN_NOTES = 0.6
# Probability that a route note chain will have notes
PROBABILITY_ROUTE_CHAIN_NOTES = 0.4
# Max notes per location chain
MAX_LOCATION_CHAIN_NOTES = 3
# Max notes per route chain
MAX_ROUTE_CHAIN_NOTES = 2
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
# Number of years back to generate driver history for
HISTORY_YEARS_BACK = 2
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
# Minimum kilometers driven in driver history (per year)
DRIVER_HISTORY_KM_MIN = 500
# Maximum kilometers driven in driver history (per year)
DRIVER_HISTORY_KM_MAX = 3000
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
# Minimum default capacity for admin info
DEFAULT_CAP_MIN = 10
# Maximum default capacity for admin info
DEFAULT_CAP_MAX = 20

# Time constants
# Default route start time (HH:MM:SS format)
ROUTE_START_TIME = "08:00:00"

# Location group schedule (weekday mapping)
LOCATION_GROUP_SCHEDULE = {
    "Schools": 4,
    "Tuesday A": 1,
    "Tuesday B": 1,
    "Wednesday A": 2,
    "Wednesday B": 2,
    "Thursday A": 3,
    "Thursday B": 3,
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
) -> str:
    """Create or update a Firebase user so it is always loginable with the given credentials."""
    full_name = f"{first_name} {last_name}"
    try:
        auth.get_user(uid)
        auth.update_user(
            uid,
            email=email,
            password=password,
            email_verified=True,
            display_name=full_name,
        )
        print(f"  Firebase user {uid} ({email}) already exists, updated")
    except auth.UserNotFoundError:
        auth.create_user(
            uid=uid,
            email=email,
            password=password,
            email_verified=True,
            display_name=full_name,
        )
        print(f"  Firebase user {uid} ({email}) created")
    auth.set_custom_user_claims(
        uid,
        {"role": role, "given_name": first_name, "family_name": last_name},
    )
    return uid


def generate_valid_phone() -> str:
    """Generate a valid phone number in E164 format"""
    # Valid Canadian area codes (Ontario and Quebec)
    valid_area_codes = [416, 647, 437, 514, 613, 905, 289, 519, 226, 705, 807, 343, 365]

    # Keep trying until we get a valid number
    max_attempts = 100
    for _ in range(max_attempts):
        area_code = random.choice(valid_area_codes)
        exchange = random.randint(200, 999)  # Exchange code (3 digits)
        number = random.randint(1000, 9999)  # Last 4 digits
        phone_str = f"+1{area_code}{exchange:03d}{number:04d}"

        try:
            parsed = phonenumbers.parse(phone_str, None)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
        except Exception:
            continue

    # Fallback: return a known valid number if we can't generate one
    return "+14165551234"


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
    ):
        self.cluster_idx = cluster_idx
        self.ordered_location_ids = ordered_location_ids
        self.cluster_locations = cluster_locations
        self.length_km = length_km


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
        plans.append(
            ClusterPlan(
                cluster_idx=cluster_idx,
                ordered_location_ids=route_order,
                cluster_locations=cluster_locations,
                length_km=round(total_length, 2),
            )
        )
    return plans


def pick_assignment_ratio(drive_date: datetime, today: date) -> float:
    """Date-bucketed driver-assignment density (mirrors old DriverAssignment seed)."""
    drive_date_only = drive_date.date()
    if drive_date_only < today:
        return ASSIGNMENT_RATIO_PAST_ROUTES
    if drive_date_only <= today + timedelta(days=NEXT_WEEK_DAYS):
        return ASSIGNMENT_RATIO_NEXT_WEEK
    return ASSIGNMENT_RATIO_FUTURE_ROUTES


def materialize_route_for_group(
    session: Session,
    route_group: RouteGroup,
    plan: ClusterPlan,
    *,
    drive_date: datetime,
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

    route = Route(
        name=f"Route {plan.cluster_idx + 1}",
        notes=fake.sentence() if random.random() < PROBABILITY_ROUTE_NOTES else "",
        length=plan.length_km,
        route_group_id=route_group.route_group_id,
        driver_id=driver_id,
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
    if drive_date.date() < today:
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
                phone_number=loc.phone_primary,
                num_children=loc.num_children,
                notes=loc.notes,
                latitude=loc.latitude,
                longitude=loc.longitude,
            )
            set_timestamps(stop_snap)
            session.add(stop_snap)

    return route


def main() -> None:
    """Main seeding function"""
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
                "notes",
                "note_chain_reads",
                "driver_history",
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
                        delivery_type = (
                            DeliveryTypeEnum.SCHOOL
                            if is_school
                            else DeliveryTypeEnum.FAMILY
                        )

                        contact_name = fake.name()
                        location = Location(
                            location_group_id=uuid.UUID(group_id),
                            name=f"{fake.company()} School"
                            if is_school
                            else contact_name,
                            contact_name=contact_name,
                            address=address,
                            phone_primary=generate_valid_phone(),
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
                            notes=fake.sentence()
                            if random.random() < PROBABILITY_LOCATION_NOTES
                            else "",
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
                matching_groups = [
                    name
                    for name, target_weekday in LOCATION_GROUP_SCHEDULE.items()
                    if target_weekday == weekday
                ]

                for group_name in matching_groups:
                    loc_group_id = group_ids.get(group_name)
                    if not loc_group_id:
                        continue
                    plans = cluster_plans_by_group.get(loc_group_id, [])
                    if not plans:
                        continue

                    drive_date = datetime.combine(current_date, datetime.min.time())
                    route_group = RouteGroup(
                        name=f"{group_name} - {current_date.strftime('%Y-%m-%d')}",
                        notes=f"Route group for {group_name} on {current_date}",
                        drive_date=drive_date,
                    )
                    set_timestamps(route_group)
                    session.add(route_group)
                    session.flush()  # need route_group_id

                    for plan in plans:
                        materialize_route_for_group(
                            session,
                            route_group,
                            plan,
                            drive_date=drive_date,
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
                            user_id=None,
                            message=fake.sentence(),
                            is_system=random.choice([True, False]),
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
                            user_id=None,
                            message=fake.sentence(),
                            is_system=True,
                        )
                        set_timestamps(note)
                        session.add(note)
                        route_notes_created += 1

            session.commit()
            print(
                f"Created {route_chains_created} route note chains "
                f"with {route_notes_created} notes"
            )

            # Create driver history
            print("Creating driver history...")
            history_entries = 0
            current_year = datetime.now().year
            years = [current_year - HISTORY_YEARS_BACK, current_year - 1, current_year]

            all_drivers_result = session.execute(
                text("SELECT driver_id FROM drivers")
            ).fetchall()

            for driver_row in all_drivers_result:
                valid_years = [y for y in years if 2025 <= y <= 2100]
                if not valid_years:
                    valid_years = [current_year]

                driver_years = random.sample(
                    valid_years, random.randint(1, len(valid_years))
                )

                for year in driver_years:
                    if (
                        year == current_year
                        and random.random() < PROBABILITY_SKIP_CURRENT_YEAR_HISTORY
                    ):
                        continue

                    months = random.sample(range(1, 13), random.randint(3, 12))

                    for month in months:
                        driver_history = DriverHistory(
                            driver_id=driver_row[0],
                            year=year,
                            month=month,
                            km=round(
                                random.uniform(
                                    DRIVER_HISTORY_KM_MIN,
                                    DRIVER_HISTORY_KM_MAX,
                                ),
                                2,
                            ),
                        )

                        set_timestamps(driver_history)
                        session.add(driver_history)
                        history_entries += 1

            session.commit()
            print(f"Created {history_entries} driver history entries")

            # Create jobs (linked to past route groups)
            print("Creating jobs...")
            past_route_groups = session.execute(
                text(
                    """
                    SELECT route_group_id, drive_date
                    FROM route_groups
                    WHERE drive_date < NOW()
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
                    started_at = drive_date + timedelta(
                        hours=random.randint(JOB_START_HOUR_MIN, JOB_START_HOUR_MAX)
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
                default_cap=random.randint(DEFAULT_CAP_MIN, DEFAULT_CAP_MAX),
                route_start_time=route_start_time_obj,
                warehouse_location=WAREHOUSE_ADDRESS,
                warehouse_longitude=WAREHOUSE_LON,
                warehouse_latitude=WAREHOUSE_LAT,
                boxes_per_car=10,
                dropoff_minutes=3,
                children_per_box=2,
                contact_name="Emily Loro",
                contact_phone=generate_valid_phone(),
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

            # Create admin accounts
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

            # Create read tracking entries for some drivers
            print("Creating note chain read tracking entries...")
            read_entries_created = 0
            all_driver_users = session.execute(
                text(
                    "SELECT u.user_id FROM users u JOIN drivers d ON u.user_id = d.user_id"
                )
            ).fetchall()

            all_chain_ids = session.execute(
                text("SELECT note_chain_id FROM note_chains")
            ).fetchall()

            for driver_user_row in all_driver_users:
                num_chains_to_read = random.randint(0, min(5, len(all_chain_ids)))
                if num_chains_to_read > 0:
                    chains_to_read = random.sample(all_chain_ids, num_chains_to_read)
                    for chain_row in chains_to_read:
                        read_entry = NoteChainReadModel(
                            note_chain_id=chain_row[0],
                            user_id=driver_user_row[0],
                            last_read_at=datetime.now(
                                ZoneInfo("America/New_York")
                            ).replace(tzinfo=None)
                            - timedelta(hours=random.randint(0, 72)),
                        )
                        set_timestamps(read_entry)
                        session.add(read_entry)
                        read_entries_created += 1

            session.commit()
            print(f"Created {read_entries_created} note chain read tracking entries")

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
                posted_at = datetime.now(ZoneInfo("America/New_York")).replace(
                    tzinfo=None
                ) - timedelta(days=days_ago)
                announcement.created_at = posted_at
                announcement.updated_at = posted_at
                session.add(announcement)
            session.commit()
            print(f"Created {len(SAMPLE_ANNOUNCEMENTS)} sample announcements")

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
    main()

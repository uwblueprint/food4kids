#!/usr/bin/env python3
"""
Comprehensive database seeding script with advanced features.
"""

import csv
import os
import random
import uuid
from datetime import datetime, timedelta
from typing import cast

import faker
import phonenumbers
from phonenumbers import PhoneNumberFormat
from sklearn.cluster import KMeans  # type: ignore[import-untyped]
from sqlalchemy import create_engine, not_, text
from sqlmodel import Session, select

# Import all models to register them with SQLModel
from app.models.admin import Admin
from app.models.base import BaseModel
from app.models.driver import Driver
from app.models.driver_assignment import DriverAssignment
from app.models.driver_history import DriverHistory
from app.models.enum import ProgressEnum
from app.models.job import Job
from app.models.location import Location
from app.models.location_group import LocationGroup
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_group_membership import RouteGroupMembership
from app.models.route_stop import RouteStop

# Initialize Faker
fake = faker.Faker()

# Configuration constants
# Percentage of locations that will be unassigned to any location group
UNASSIGNED_LOCATION_PERCENTAGE = 0.05
# Average number of stops per route (used to calculate number of clusters)
AVG_STOPS_PER_ROUTE = 7.5
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
# Probability that a driver will have notes
PROBABILITY_DRIVER_NOTES = 0.3
# Probability to skip creating driver history for the current year
PROBABILITY_SKIP_CURRENT_YEAR_HISTORY = 0.2

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
# Minimum number of boxes at a location
NUM_BOXES_MIN = 1
# Maximum number of boxes at a location
NUM_BOXES_MAX = 5
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

# Database connection
DATABASE_URL = "postgresql://postgres:postgres@f4k_db:5432/f4k"


def set_timestamps(instance: BaseModel) -> None:
    """Set updated_at to match created_at for seed data"""
    if instance.created_at is not None and instance.updated_at is None:
        instance.updated_at = instance.created_at


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


def create_route_and_stops(
    session: Session,
    route_id: str,
    route_order: list[str],
    cluster_idx: int,
    total_length: float,
) -> None:
    """Create route and its stops in the database"""
    route = Route(
        route_id=uuid.UUID(route_id),
        name=f"Route {cluster_idx + 1}",
        notes=fake.sentence() if random.random() < PROBABILITY_ROUTE_NOTES else "",
        length=round(total_length, 2),
    )
    set_timestamps(route)
    session.add(route)

    for stop_num, location_id in enumerate(route_order, 1):
        route_stop = RouteStop(
            route_id=uuid.UUID(route_id),
            location_id=uuid.UUID(location_id),
            stop_number=stop_num,
        )
        set_timestamps(route_stop)
        session.add(route_stop)


def create_routes_for_group(session: Session, group_locations: list[Location]) -> int:
    """Create routes for a location group using clustering and TSP"""
    if len(group_locations) < 2:
        return 0

    num_clusters = max(1, int(len(group_locations) // AVG_STOPS_PER_ROUTE))
    clusters = create_clusters(group_locations, num_clusters)
    routes_created = 0

    for cluster_idx, cluster_locations in enumerate(clusters):
        if not cluster_locations:
            continue

        # All locations in seed script should have coordinates
        for loc in cluster_locations:
            assert loc.latitude is not None and loc.longitude is not None, (
                f"Location {loc.location_id} is missing coordinates"
            )

        # Type narrowing: after assert, we know coordinates are not None
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

        route_id = str(uuid.uuid4())
        create_route_and_stops(
            session, route_id, route_order, cluster_idx, total_length
        )
        routes_created += 1

    return routes_created


def main() -> None:
    """Main seeding function"""
    print("Starting final database seeding...")

    # Create database connection
    engine = create_engine(DATABASE_URL, echo=False)

    with Session(engine) as session:
        try:
            # Clear existing data
            print("Clearing existing data...")
            tables_to_clear = [
                "driver_assignments",
                "driver_history",
                "jobs",
                "route_group_memberships",
                "route_stops",
                "routes",
                "route_groups",
                "locations",
                "location_groups",
                "drivers",
                "admin_info",
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
            group_ids = {}
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
            csv_path = "app/data/locations.csv"
            locations_created = 0

            non_school_groups = [
                gid for name, gid in group_ids.items() if name != "Schools"
            ]

            if os.path.exists(csv_path):
                with open(csv_path) as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        address = row.get("formatted_address", "")
                        lat, lon = (
                            float(row.get("latitude", 0)),
                            float(row.get("longitude", 0)),
                        )

                        # Determine location group
                        group_id: str | None
                        if random.random() < UNASSIGNED_LOCATION_PERCENTAGE:
                            group_id = None
                        else:
                            # Check for small cities that need specific group assignments
                            is_small_city = any(
                                city in address.lower() for city in SMALL_CITIES
                            )

                            if is_small_city:
                                # Random assignment from non-school groups for small cities
                                group_id = random.choice(non_school_groups)
                            else:
                                # Random assignment for other locations
                                group_id = random.choice(list(group_ids.values()))

                        # Generate fake data for location insertion
                        is_school = random.choice([True, False])
                        location = Location(
                            location_group_id=uuid.UUID(group_id) if group_id else None,
                            school_name=fake.company() + " School"
                            if is_school
                            else None,
                            contact_name=fake.name(),
                            address=address,
                            phone_number=generate_valid_phone(),
                            longitude=lon,
                            latitude=lat,
                            halal=random.choice([True, False]),
                            dietary_restrictions=fake.sentence()
                            if random.random() < PROBABILITY_DIETARY_RESTRICTIONS
                            else "",
                            num_children=random.randint(
                                NUM_CHILDREN_MIN, NUM_CHILDREN_MAX
                            )
                            if random.random() < PROBABILITY_NUM_CHILDREN
                            else None,
                            num_boxes=random.randint(NUM_BOXES_MIN, NUM_BOXES_MAX),
                            notes=fake.sentence()
                            if random.random() < PROBABILITY_LOCATION_NOTES
                            else "",
                        )
                        set_timestamps(location)
                        session.add(location)
                        locations_created += 1
            else:
                raise FileNotFoundError(f"Locations CSV file not found at {csv_path}")

            # Warehouse location is not stored in database - it's the implicit starting point for all routes

            session.commit()
            print(f"Created {locations_created} locations")

            # Create routes
            print("Creating routes...")
            routes_created = 0

            # Get all locations with a location group assigned
            locations_with_group = session.exec(
                select(Location).where(
                    not_(Location.location_group_id.is_(None))  # type: ignore[union-attr]
                )
            ).all()

            # Group locations by location group
            locations_by_group: dict[str, list[Location]] = {}
            for location in locations_with_group:
                # Type narrowing: we filtered for non-None location_group_id in the query
                assert location.location_group_id is not None
                group_id = str(location.location_group_id)
                if group_id not in locations_by_group:
                    locations_by_group[group_id] = []
                locations_by_group[group_id].append(location)

            for _, group_locations in locations_by_group.items():
                routes_created += create_routes_for_group(session, group_locations)

            session.commit()
            print(f"Created {routes_created} routes")

            # Create drivers
            print("Creating drivers...")
            num_drivers = max(routes_created, MIN_DRIVERS)
            drivers_created = 0

            for _ in range(num_drivers):
                # Create a single driver with fake data
                driver = Driver(
                    auth_id=f"seed_driver_{uuid.uuid4().hex[:8]}",
                    name=fake.name(),
                    email=fake.email(),
                    phone=generate_valid_phone(),
                    address=fake.address(),
                    license_plate=fake.license_plate(),
                    car_make_model=fake.word().title() + " " + fake.word().title(),
                    active=random.choice([True, False]),
                    notes=fake.sentence()
                    if random.random() < PROBABILITY_DRIVER_NOTES
                    else "",
                )
                set_timestamps(driver)
                session.add(driver)
                drivers_created += 1

            session.commit()
            print(f"Created {drivers_created} drivers")

            # Create route groups
            print("Creating route groups...")
            route_groups_created = 0
            today = datetime.now().date()

            # Generate dates for past and future months
            start_date = today - timedelta(days=MONTHS_PAST * DAYS_PER_MONTH)
            end_date = today + timedelta(days=MONTHS_FUTURE * DAYS_PER_MONTH)

            current_date = start_date
            while current_date <= end_date:
                weekday = current_date.weekday()  # 0=Monday, 6=Sunday

                # Find matching location groups for this weekday
                matching_groups = [
                    name
                    for name, target_weekday in LOCATION_GROUP_SCHEDULE.items()
                    if target_weekday == weekday
                ]

                for group_name in matching_groups:
                    loc_group_id_for_route: str | None = group_ids.get(group_name)
                    if not loc_group_id_for_route:
                        continue

                    # Create route group for a specific date and location group
                    group_routes = session.execute(
                        text(
                            "SELECT DISTINCT r.route_id FROM routes r JOIN route_stops rs ON r.route_id = rs.route_id JOIN locations l ON rs.location_id = l.location_id WHERE l.location_group_id = :group_id"
                        ),
                        {"group_id": loc_group_id_for_route},
                    ).fetchall()

                    if not group_routes:
                        continue

                    route_group = RouteGroup(
                        name=f"{group_name} - {current_date.strftime('%Y-%m-%d')}",
                        notes=f"Route group for {group_name} on {current_date}",
                        drive_date=datetime.combine(current_date, datetime.min.time()),
                    )
                    set_timestamps(route_group)
                    session.add(route_group)
                    session.flush()  # Flush to get the route_group_id

                    for route in group_routes:
                        membership = RouteGroupMembership(
                            route_group_id=route_group.route_group_id,
                            route_id=route.route_id,
                        )
                        set_timestamps(membership)
                        session.add(membership)
                    route_groups_created += 1

                current_date += timedelta(days=1)

            session.commit()
            print(f"Created {route_groups_created} route groups")

            # Create driver assignments
            print("Creating driver assignments...")
            assignments_created = 0
            active_drivers_result = session.execute(
                text("SELECT driver_id FROM drivers WHERE active = TRUE")
            ).fetchall()

            if not active_drivers_result:
                print("Warning: No active drivers found")
            else:
                # Get all route groups with their routes
                route_group_data = session.execute(
                    text("""
                        SELECT rg.route_group_id, rg.drive_date, r.route_id
                        FROM route_groups rg
                        JOIN route_group_memberships rgm ON rg.route_group_id = rgm.route_group_id
                        JOIN routes r ON rgm.route_id = r.route_id
                        ORDER BY rg.drive_date
                    """)
                ).fetchall()

                for route_group_id, drive_date, route_id in route_group_data:
                    drive_date_obj = drive_date.date()

                    # Determine assignment strategy based on date
                    if drive_date_obj < today:
                        # Past routes: assign all
                        assignment_ratio = ASSIGNMENT_RATIO_PAST_ROUTES
                    elif drive_date_obj <= today + timedelta(days=NEXT_WEEK_DAYS):
                        # Next week: assign most
                        assignment_ratio = ASSIGNMENT_RATIO_NEXT_WEEK
                    else:
                        # Future routes: partial assignment
                        assignment_ratio = ASSIGNMENT_RATIO_FUTURE_ROUTES

                    if random.random() < assignment_ratio:
                        driver_row = random.choice(active_drivers_result)
                        assignment = DriverAssignment(
                            driver_id=driver_row[0],  # Access first column (driver_id)
                            route_id=route_id,
                            route_group_id=route_group_id,
                            time=drive_date,
                            completed=drive_date_obj < today,
                        )
                        set_timestamps(assignment)
                        session.add(assignment)
                        assignments_created += 1

            session.commit()
            print(f"Created {assignments_created} driver assignments")

            # Create driver history
            print("Creating driver history...")
            history_entries = 0
            current_year = datetime.now().year
            years = [current_year - HISTORY_YEARS_BACK, current_year - 1, current_year]

            all_drivers_result = session.execute(
                text("SELECT driver_id FROM drivers")
            ).fetchall()
            for driver_row in all_drivers_result:
                # Filter years to only include valid ones (2025-2100)
                valid_years = [y for y in years if 2025 <= y <= 2100]
                if not valid_years:
                    valid_years = [current_year]  # At least use current year
                driver_years = random.sample(
                    valid_years, random.randint(1, len(valid_years))
                )
                for year in driver_years:
                    if (
                        year == current_year
                        and random.random() < PROBABILITY_SKIP_CURRENT_YEAR_HISTORY
                    ):
                        continue
                    driver_history = DriverHistory(
                        driver_id=driver_row[0],  # Access first column (driver_id)
                        year=year,
                        km=round(
                            random.uniform(
                                DRIVER_HISTORY_KM_MIN, DRIVER_HISTORY_KM_MAX
                            ),
                            2,
                        ),
                    )
                    set_timestamps(driver_history)
                    session.add(driver_history)
                    history_entries += 1

            session.commit()
            print(f"Created {history_entries} driver history entries")

            # Create jobs
            print("Creating jobs...")
            # Get past route groups
            past_route_groups = session.execute(
                text("""
                    SELECT route_group_id, drive_date 
                    FROM route_groups 
                    WHERE drive_date < NOW()
                    ORDER BY drive_date DESC
                    LIMIT :limit
                """),
                {"limit": PAST_ROUTE_GROUPS_LIMIT},
            ).fetchall()

            if past_route_groups:
                num_jobs = random.randint(
                    MIN_JOBS, min(MAX_JOBS, len(past_route_groups))
                )
                selected_groups = random.sample(past_route_groups, num_jobs)

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
            print(f"Created {len(past_route_groups) if past_route_groups else 0} jobs")

            # Create admin info
            print("Creating admin info...")
            # Parse route_start_time string to time object
            route_start_time_obj = datetime.strptime(
                ROUTE_START_TIME, "%H:%M:%S"
            ).time()
            admin = Admin(
                admin_name=fake.name(),
                default_cap=random.randint(DEFAULT_CAP_MIN, DEFAULT_CAP_MAX),
                admin_phone=generate_valid_phone(),
                admin_email=fake.email(),
                route_start_time=route_start_time_obj,
                warehouse_location=WAREHOUSE_ADDRESS,
            )
            set_timestamps(admin)
            session.add(admin)

            session.commit()
            print("Created admin info")
            print("Comprehensive database seeding completed successfully!")

        except Exception as e:
            print(f"Error during seeding: {e}")
            session.rollback()
            raise


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Comprehensive database seeding script with advanced features.
"""

import csv
import os
import random
import uuid
from datetime import datetime, timedelta

import faker  # type: ignore
from sklearn.cluster import KMeans  # type: ignore
from sqlalchemy import create_engine, text  # type: ignore
from sqlmodel import Session  # type: ignore

# Initialize Faker
fake = faker.Faker()

# Configuration constants
UNASSIGNED_LOCATION_PERCENTAGE = 0.05
AVG_STOPS_PER_ROUTE = 7.5
MONTHS_PAST = 2
MONTHS_FUTURE = 1

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
    """Get database URL for seeding (synchronous connection)"""
    return "postgresql://postgres:postgres@f4k_db:5432/f4k"


def execute_insert(session, table: str, data: dict) -> None:
    """Helper function to execute INSERT statements with common patterns"""
    columns = ", ".join(data)
    placeholders = ", ".join(f":{key}" for key in data)
    session.execute(
        text(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"), data
    )


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
    r = 6371  # Earth's radius in km
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


def create_clusters(group_locations: list, num_clusters: int) -> list[list]:
    """Create clusters from group locations using k-means or simple grouping"""
    if len(group_locations) <= num_clusters:
        return [group_locations]

    coords = [(loc.latitude, loc.longitude) for loc in group_locations]
    # TODO: Eventually write our own implementation or different algorithm to avoid using scikit-learn
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(coords)

    clusters: list[list] = [[] for _ in range(num_clusters)]
    for i, location in enumerate(group_locations):
        clusters[cluster_labels[i]].append(location)

    return clusters


def calculate_route_length(
    route_order: list[str],
    cluster_locations: list,
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
        dist = haversine_distance(
            prev_lat, prev_lon, location.latitude, location.longitude
        )
        total_length += dist
        prev_lat, prev_lon = location.latitude, location.longitude

    return total_length


def create_route_and_stops(
    session,
    route_id: str,
    route_order: list[str],
    cluster_idx: int,
    total_length: float,
) -> None:
    """Create route and its stops in the database"""
    execute_insert(
        session,
        "routes",
        {
            "route_id": route_id,
            "name": f"Route {cluster_idx + 1}",
            "notes": fake.sentence() if random.random() < 0.1 else "",
            "length": round(total_length, 2),
            "created_at": "NOW()",
            "updated_at": "NOW()",
        },
    )

    for stop_num, location_id in enumerate(route_order, 1):
        execute_insert(
            session,
            "route_stops",
            {
                "route_stop_id": str(uuid.uuid4()),
                "route_id": route_id,
                "location_id": location_id,
                "stop_number": stop_num,
                "created_at": "NOW()",
                "updated_at": "NOW()",
            },
        )


def create_routes_for_group(session, group_locations: list) -> int:
    """Create routes for a location group using clustering and TSP"""
    if len(group_locations) < 2:
        return 0

    num_clusters = max(1, int(len(group_locations) // AVG_STOPS_PER_ROUTE))
    clusters = create_clusters(group_locations, num_clusters)
    routes_created = 0

    for cluster_idx, cluster_locations in enumerate(clusters):
        if not cluster_locations:
            continue

        tsp_locations = [
            (loc.latitude, loc.longitude, str(loc.location_id))
            for loc in cluster_locations
        ]
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


def main():
    """Main seeding function"""
    print("Starting final database seeding...")

    # Create database connection
    database_url = get_database_url()
    engine = create_engine(database_url, echo=False)

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
                group_id = str(uuid.uuid4())
                data = {
                    "location_group_id": group_id,
                    "name": name,
                    "color": fake.hex_color(),
                    "notes": "",
                    "created_at": "NOW()",
                    "updated_at": "NOW()",
                }
                execute_insert(session, "location_groups", data)
                group_ids[name] = group_id

            session.commit()
            print(f"Created {len(group_names)} location groups")

            # Create locations from CSV
            print("Creating locations from CSV...")
            csv_path = "app/data/locations.csv"
            locations_created = 0

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
                        if random.random() < UNASSIGNED_LOCATION_PERCENTAGE:
                            group_id = None
                        else:
                            # Check for small cities that need specific group assignments
                            is_small_city = any(
                                city in address.lower() for city in SMALL_CITIES
                            )

                            if is_small_city:
                                # Random assignment from non-school groups for small cities
                                non_school_groups = [
                                    gid
                                    for name, gid in group_ids.items()
                                    if name != "Schools"
                                ]
                                group_id = random.choice(non_school_groups)
                            else:
                                # Random assignment for other locations
                                group_id = random.choice(list(group_ids.values()))

                        # Generate fake data for location insertion
                        is_school = random.choice([True, False])
                        data = {
                            "location_id": str(uuid.uuid4()),
                            "location_group_id": group_id,
                            "is_school": is_school,
                            "school_name": fake.company() + " School"
                            if is_school
                            else None,
                            "contact_name": fake.name(),
                            "address": address,
                            "phone_number": fake.numerify("+1212#######"),
                            "longitude": lon,
                            "latitude": lat,
                            "halal": random.choice([True, False]),
                            "dietary_restrictions": fake.sentence()
                            if random.random() < 0.3
                            else None,
                            "num_children": random.randint(1, 4)
                            if random.random() < 0.8
                            else None,
                            "num_boxes": random.randint(1, 5),
                            "notes": fake.sentence() if random.random() < 0.4 else "",
                            "created_at": "NOW()",
                            "updated_at": "NOW()",
                        }
                        execute_insert(session, "locations", data)
                        locations_created += 1
            else:
                raise FileNotFoundError(f"Locations CSV file not found at {csv_path}")

            # Warehouse location is not stored in database - it's the implicit starting point for all routes

            session.commit()
            print(f"Created {locations_created} locations")

            # Create routes
            print("Creating routes...")
            routes_created = 0

            # Get all locations grouped by location group
            location_groups = session.execute(
                text("""
                SELECT location_group_id, location_id, latitude, longitude 
                FROM locations 
                WHERE location_group_id IS NOT NULL
                ORDER BY location_group_id
            """)
            ).fetchall()

            # Group locations by location group
            locations_by_group: dict[str, list] = {}
            for row in location_groups:
                group_id = str(row.location_group_id)
                if group_id not in locations_by_group:
                    locations_by_group[group_id] = []
                locations_by_group[group_id].append(row)

            for _, group_locations in locations_by_group.items():
                routes_created += create_routes_for_group(session, group_locations)

            session.commit()
            print(f"Created {routes_created} routes")

            # Create drivers
            print("Creating drivers...")
            num_drivers = max(routes_created, 5)
            drivers_created = 0

            for _ in range(num_drivers):
                # Create a single driver with fake data
                data = {
                    "driver_id": str(uuid.uuid4()),
                    "auth_id": f"seed_driver_{uuid.uuid4().hex[:8]}",
                    "name": fake.name(),
                    "email": fake.email(),
                    "phone": fake.numerify("+1212#######"),
                    "address": fake.address(),
                    "license_plate": fake.license_plate(),
                    "car_make_model": fake.word().title() + " " + fake.word().title(),
                    "active": random.choice([True, False]),
                    "notes": fake.sentence() if random.random() < 0.3 else "",
                    "created_at": "NOW()",
                    "updated_at": "NOW()",
                }
                execute_insert(session, "drivers", data)
                drivers_created += 1

            session.commit()
            print(f"Created {drivers_created} drivers")

            # Create route groups
            print("Creating route groups...")
            route_groups_created = 0
            today = datetime.now().date()

            # Generate dates for past and future months
            start_date = today - timedelta(days=MONTHS_PAST * 30)
            end_date = today + timedelta(days=MONTHS_FUTURE * 30)

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
                    group_id = group_ids.get(group_name)
                    if not group_id:
                        continue

                    # Create route group for a specific date and location group
                    group_routes = session.execute(
                        text(
                            "SELECT DISTINCT r.route_id FROM routes r JOIN route_stops rs ON r.route_id = rs.route_id JOIN locations l ON rs.location_id = l.location_id WHERE l.location_group_id = :group_id"
                        ),
                        {"group_id": group_id},
                    ).fetchall()

                    if not group_routes:
                        continue

                    route_group_id = str(uuid.uuid4())
                    execute_insert(
                        session,
                        "route_groups",
                        {
                            "route_group_id": route_group_id,
                            "name": f"{group_name} - {current_date.strftime('%Y-%m-%d')}",
                            "notes": f"Route group for {group_name} on {current_date}",
                            "drive_date": datetime.combine(
                                current_date, datetime.min.time()
                            ),
                        },
                    )

                    for route in group_routes:
                        execute_insert(
                            session,
                            "route_group_memberships",
                            {
                                "route_group_membership_id": str(uuid.uuid4()),
                                "route_group_id": route_group_id,
                                "route_id": route.route_id,
                            },
                        )
                    route_groups_created += 1

                current_date += timedelta(days=1)

            session.commit()
            print(f"Created {route_groups_created} route groups")

            # Create driver assignments
            print("Creating driver assignments...")
            assignments_created = 0
            active_drivers = session.execute(
                text("SELECT driver_id FROM drivers WHERE active = TRUE")
            ).fetchall()

            if not active_drivers:
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

                for _, drive_date, route_id in route_group_data:
                    drive_date_obj = drive_date.date()

                    # Determine assignment strategy based on date
                    if drive_date_obj < today:
                        # Past routes: assign all
                        assignment_ratio = 1.0
                    elif drive_date_obj <= today + timedelta(days=7):
                        # Next week: assign most
                        assignment_ratio = 0.8
                    else:
                        # Future routes: partial assignment
                        assignment_ratio = 0.4

                    if random.random() < assignment_ratio:
                        driver = random.choice(active_drivers)
                        execute_insert(
                            session,
                            "driver_assignments",
                            {
                                "driver_assignment_id": str(uuid.uuid4()),
                                "driver_id": driver.driver_id,
                                "route_id": route_id,
                                "time": drive_date,
                                "completed": drive_date_obj < today,
                            },
                        )
                        assignments_created += 1

            session.commit()
            print(f"Created {assignments_created} driver assignments")

            # Create driver history
            print("Creating driver history...")
            history_entries = 0
            current_year = datetime.now().year
            years = [current_year - 2, current_year - 1, current_year]

            all_drivers = session.execute(
                text("SELECT driver_id FROM drivers")
            ).fetchall()
            for driver in all_drivers:
                driver_years = random.sample(years, random.randint(1, len(years)))
                for year in driver_years:
                    if year == current_year and random.random() < 0.2:
                        continue
                    execute_insert(
                        session,
                        "driver_history",
                        {
                            "driver_id": driver.driver_id,
                            "year": year,
                            "km": round(random.uniform(500, 3000), 2),
                        },
                    )
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
                    LIMIT 5
                """)
            ).fetchall()

            if past_route_groups:
                num_jobs = random.randint(3, min(5, len(past_route_groups)))
                selected_groups = random.sample(past_route_groups, num_jobs)

                for route_group_id, drive_date in selected_groups:
                    started_at = drive_date + timedelta(hours=random.randint(8, 10))
                    updated_at = started_at + timedelta(hours=random.randint(1, 3))
                    finished_at = updated_at + timedelta(hours=random.randint(1, 4))

                    execute_insert(
                        session,
                        "jobs",
                        {
                            "job_id": str(uuid.uuid4()),
                            "route_group_id": route_group_id,
                            "progress": "COMPLETED",
                            "started_at": started_at,
                            "updated_at": updated_at,
                            "finished_at": finished_at,
                        },
                    )

            session.commit()
            print(f"Created {len(past_route_groups) if past_route_groups else 0} jobs")

            # Create admin info
            print("Creating admin info...")
            execute_insert(
                session,
                "admin_info",
                {
                    "admin_id": str(uuid.uuid4()),
                    "admin_name": fake.name(),
                    "default_cap": random.randint(20, 50),
                    "admin_phone": fake.numerify("+1212#######"),
                    "admin_email": fake.email(),
                    "route_start_time": "08:00:00",
                    "warehouse_location": WAREHOUSE_ADDRESS,
                    "created_at": "NOW()",
                    "updated_at": "NOW()",
                },
            )

            session.commit()
            print("Created admin info")
            print("Comprehensive database seeding completed successfully!")

        except Exception as e:
            print(f"Error during seeding: {e}")
            session.rollback()
            raise


if __name__ == "__main__":
    main()

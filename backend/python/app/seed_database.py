#!/usr/bin/env python3
"""
Comprehensive database seeding script with advanced features.
"""

import csv
import os
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import faker  # type: ignore
from sklearn.cluster import KMeans  # type: ignore
from sqlalchemy import create_engine, text  # type: ignore
from sqlmodel import Session  # type: ignore

# Initialize Faker
fake = faker.Faker()

# Configuration constants
UNASSIGNED_LOCATION_PERCENTAGE = 0.05
AVG_STOPS_PER_ROUTE = 7.5
DRIVER_TO_ROUTE_RATIO = 0.75
MONTHS_PAST = 2
MONTHS_FUTURE = 1

# Location group schedule (weekday mapping)
LOCATION_GROUP_SCHEDULE = {
    "Schools": 4,  # Friday
    "Tuesday A": 1,  # Tuesday
    "Tuesday B": 1,  # Tuesday
    "Wednesday A": 2,  # Wednesday
    "Wednesday B": 2,  # Wednesday
    "Thursday A": 3,  # Thursday
    "Thursday B": 3,  # Thursday
}

# Warehouse location
WAREHOUSE_LAT = 43.402343
WAREHOUSE_LON = -80.464610
WAREHOUSE_ADDRESS = "330 Trillium Drive, Kitchener, ON"


def get_database_url() -> str:
    """Get database URL for seeding (synchronous connection)"""
    return "postgresql://postgres:postgres@f4k_db:5432/f4k"


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate haversine distance between two points in km"""
    from math import radians, cos, sin, asin, sqrt

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
    locations: List[Tuple[float, float, str]],
) -> List[str]:
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
            groups = [
                {"name": "Schools", "color": fake.hex_color()},
                {"name": "Tuesday A", "color": fake.hex_color()},
                {"name": "Tuesday B", "color": fake.hex_color()},
                {"name": "Wednesday A", "color": fake.hex_color()},
                {"name": "Wednesday B", "color": fake.hex_color()},
                {"name": "Thursday A", "color": fake.hex_color()},
                {"name": "Thursday B", "color": fake.hex_color()},
            ]

            group_ids = {}
            for group_data in groups:
                group_id = str(uuid.uuid4())
                session.execute(
                    text("""
                        INSERT INTO location_groups (location_group_id, name, color, notes, created_at, updated_at)
                        VALUES (:id, :name, :color, '', NOW(), NOW())
                    """),
                    {
                        "id": group_id,
                        "name": group_data["name"],
                        "color": group_data["color"],
                    },
                )
                group_ids[group_data["name"]] = group_id

            session.commit()
            print(f"Created {len(groups)} location groups")

            # Create locations from CSV
            print("Creating locations from CSV...")
            csv_path = "app/data/locations.csv"
            locations_created = 0

            if os.path.exists(csv_path):
                non_school_groups = [
                    gid for name, gid in group_ids.items() if name != "Schools"
                ]
                cambridge_group = random.choice(non_school_groups)
                elmira_group = random.choice(non_school_groups)
                new_hamburg_group = random.choice(non_school_groups)

                with open(csv_path, "r") as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        address = row.get("formatted_address", "")
                        lat = float(row.get("latitude", 0))
                        lon = float(row.get("longitude", 0))

                        # Determine location group
                        location_group_id = None
                        if random.random() < UNASSIGNED_LOCATION_PERCENTAGE:  # 5% unassigned
                            location_group_id = None
                        elif "cambridge" in address.lower():
                            location_group_id = cambridge_group
                        elif "elmira" in address.lower():
                            location_group_id = elmira_group
                        elif "new hamburg" in address.lower():
                            location_group_id = new_hamburg_group
                        else:
                            location_group_id = random.choice(list(group_ids.values()))

                        location_id = str(uuid.uuid4())
                        is_school = random.choice([True, False])
                        school_name = fake.company() + " School" if is_school else None

                        session.execute(
                            text("""
                                INSERT INTO locations (location_id, location_group_id, is_school, school_name, 
                                                    contact_name, address, phone_number, longitude, latitude, 
                                                    halal, dietary_restrictions, num_children, num_boxes, notes,
                                                    created_at, updated_at)
                                VALUES (:id, :group_id, :is_school, :school_name, :contact_name, :address, 
                                       :phone, :lon, :lat, :halal, :dietary, :children, :boxes, :notes,
                                       NOW(), NOW())
                            """),
                            {
                                "id": location_id,
                                "group_id": location_group_id,
                                "is_school": is_school,
                                "school_name": school_name,
                                "contact_name": fake.name(),
                                "address": address,
                                "phone": fake.numerify("###-###-####"),
                                "lon": lon,
                                "lat": lat,
                                "halal": random.choice([True, False]),
                                "dietary": fake.sentence()
                                if random.random() < 0.3
                                else None,
                                "children": random.randint(1, 10)
                                if random.random() < 0.8
                                else None,
                                "boxes": random.randint(1, 5),
                                "notes": fake.sentence()
                                if random.random() < 0.4
                                else "",
                            },
                        )
                        locations_created += 1
            else:
                print(f"Warning: CSV file not found at {csv_path}")

            # Add warehouse location
            warehouse_id = str(uuid.uuid4())
            session.execute(
                text("""
                    INSERT INTO locations (location_id, location_group_id, is_school, school_name, 
                                        contact_name, address, phone_number, longitude, latitude, 
                                        halal, dietary_restrictions, num_children, num_boxes, notes,
                                        created_at, updated_at)
                    VALUES (:id, NULL, FALSE, NULL, :contact_name, :address, :phone, :lon, :lat, 
                           FALSE, NULL, NULL, 0, :notes, NOW(), NOW())
                """),
                {
                    "id": warehouse_id,
                    "contact_name": "Warehouse Manager",
                    "address": "330 Trillium Drive, Kitchener, ON",
                    "phone": fake.phone_number(),
                    "lon": -80.464610,
                    "lat": 43.402343,
                    "notes": "Main warehouse location",
                },
            )
            locations_created += 1

            session.commit()
            print(f"Created {locations_created} locations")

            # Create routes with k-means clustering
            print("Creating routes with k-means clustering...")
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
            locations_by_group: Dict[str, List] = {}
            for row in location_groups:
                group_id = str(row.location_group_id)
                if group_id not in locations_by_group:
                    locations_by_group[group_id] = []
                locations_by_group[group_id].append(row)

            for group_id, group_locations in locations_by_group.items():
                if len(group_locations) < 2:
                    continue

                # Calculate number of clusters
                num_clusters = max(1, int(len(group_locations) // AVG_STOPS_PER_ROUTE))

                # Prepare coordinates for clustering
                coords = [(loc.latitude, loc.longitude) for loc in group_locations]

                if len(coords) <= num_clusters:
                    # If we have fewer locations than clusters, just create one route
                    clusters = [group_locations]
                else:
                    # Perform k-means clustering
                    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
                    cluster_labels = kmeans.fit_predict(coords)

                    # Group locations by cluster
                    clusters = [[] for _ in range(num_clusters)]
                    for i, location in enumerate(group_locations):
                        clusters[cluster_labels[i]].append(location)

                # Create routes for each cluster
                for cluster_idx, cluster_locations in enumerate(clusters):
                    if not cluster_locations:
                        continue

                    # Prepare locations for TSP (lat, lon, location_id)
                    tsp_locations = [
                        (loc.latitude, loc.longitude, str(loc.location_id))
                        for loc in cluster_locations
                    ]

                    # Solve TSP
                    route_order = simple_tsp(
                        WAREHOUSE_LAT, WAREHOUSE_LON, tsp_locations
                    )

                    # Calculate route length
                    total_length = 0.0
                    prev_lat, prev_lon = WAREHOUSE_LAT, WAREHOUSE_LON

                    for location_id in route_order:
                        # Find location by ID
                        location = next(
                            loc
                            for loc in cluster_locations
                            if str(loc.location_id) == location_id
                        )
                        dist = haversine_distance(
                            prev_lat, prev_lon, location.latitude, location.longitude
                        )
                        total_length += dist
                        prev_lat, prev_lon = location.latitude, location.longitude

                    # Create route
                    route_id = str(uuid.uuid4())
                    session.execute(
                        text("""
                            INSERT INTO routes (route_id, name, notes, length, created_at, updated_at)
                            VALUES (:id, :name, :notes, :length, NOW(), NOW())
                        """),
                        {
                            "id": route_id,
                            "name": f"Route {cluster_idx + 1}",
                            "notes": fake.sentence() if random.random() < 0.1 else "",
                            "length": round(total_length, 2),
                        },
                    )

                    # Create route stops
                    for stop_num, location_id in enumerate(route_order, 1):
                        session.execute(
                            text("""
                                INSERT INTO route_stops (route_stop_id, route_id, location_id, stop_number, created_at, updated_at)
                                VALUES (:id, :route_id, :location_id, :stop_number, NOW(), NOW())
                            """),
                            {
                                "id": str(uuid.uuid4()),
                                "route_id": route_id,
                                "location_id": location_id,
                                "stop_number": stop_num,
                            },
                        )

                    routes_created += 1

            session.commit()
            print(f"Created {routes_created} routes")

            # Create drivers
            print("Creating drivers...")
            num_drivers = max(routes_created, 5)
            drivers_created = 0

            for i in range(num_drivers):
                driver_id = str(uuid.uuid4())
                session.execute(
                    text("""
                        INSERT INTO drivers (driver_id, auth_id, name, email, phone, address, 
                                          license_plate, car_make_model, active, notes, created_at, updated_at)
                        VALUES (:id, :auth_id, :name, :email, :phone, :address, 
                               :license, :car, :active, :notes, NOW(), NOW())
                    """),
                    {
                        "id": driver_id,
                        "auth_id": f"seed_driver_{uuid.uuid4().hex[:8]}",
                        "name": fake.name(),
                        "email": fake.email(),
                        "phone": fake.numerify("###-###-####"),
                        "address": fake.address(),
                        "license": fake.license_plate(),
                        "car": fake.word().title() + " " + fake.word().title(),
                        "active": random.choice([True, False]),
                        "notes": fake.sentence() if random.random() < 0.3 else "",
                    },
                )
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

                    # Find routes for this location group
                    group_routes = session.execute(
                        text("""
                            SELECT DISTINCT r.route_id 
                            FROM routes r
                            JOIN route_stops rs ON r.route_id = rs.route_id
                            JOIN locations l ON rs.location_id = l.location_id
                            WHERE l.location_group_id = :group_id
                        """),
                        {"group_id": group_id},
                    ).fetchall()

                    if not group_routes:
                        continue

                    # Create route group
                    route_group_id = str(uuid.uuid4())
                    session.execute(
                        text("""
                            INSERT INTO route_groups (route_group_id, name, notes, drive_date)
                            VALUES (:id, :name, :notes, :drive_date)
                        """),
                        {
                            "id": route_group_id,
                            "name": f"{group_name} - {current_date.strftime('%Y-%m-%d')}",
                            "notes": f"Route group for {group_name} on {current_date}",
                            "drive_date": datetime.combine(
                                current_date, datetime.min.time()
                            ),
                        },
                    )

                    # Create memberships
                    for route in group_routes:
                        session.execute(
                            text("""
                                INSERT INTO route_group_memberships (route_group_membership_id, route_group_id, route_id)
                                VALUES (:id, :route_group_id, :route_id)
                            """),
                            {
                                "id": str(uuid.uuid4()),
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

                for route_group_id, drive_date, route_id in route_group_data:
                    drive_date_obj = drive_date.date()

                    # Determine assignment strategy based on date
                    if drive_date_obj < today:
                        # Past routes: assign all
                        assignment_ratio = 1.0
                    elif drive_date_obj <= today + timedelta(days=7):
                        # Next week: assign all
                        assignment_ratio = 1.0
                    else:
                        # Future routes: partial assignment
                        assignment_ratio = 0.6

                    if random.random() < assignment_ratio:
                        driver = random.choice(active_drivers)
                        completed = drive_date_obj < today

                        session.execute(
                            text("""
                                INSERT INTO driver_assignments (driver_assignment_id, driver_id, route_id, time, completed)
                                VALUES (:id, :driver_id, :route_id, :time, :completed)
                            """),
                            {
                                "id": str(uuid.uuid4()),
                                "driver_id": driver.driver_id,
                                "route_id": route_id,
                                "time": drive_date,
                                "completed": completed,
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
                # Randomly determine which years this driver has history for
                driver_years = random.sample(years, random.randint(1, len(years)))

                for year in driver_years:
                    # Some drivers might have left (no recent years)
                    if year == current_year and random.random() < 0.2:
                        continue  # Skip current year for some drivers

                    km = random.uniform(500, 3000)

                    session.execute(
                        text("""
                            INSERT INTO driver_history (driver_id, year, km)
                            VALUES (:driver_id, :year, :km)
                        """),
                        {
                            "driver_id": driver.driver_id,
                            "year": year,
                            "km": round(km, 2),
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
                    # Create realistic timestamps
                    started_at = drive_date + timedelta(hours=random.randint(8, 10))
                    updated_at = started_at + timedelta(hours=random.randint(1, 3))
                    finished_at = updated_at + timedelta(hours=random.randint(1, 4))

                    session.execute(
                        text("""
                            INSERT INTO jobs (job_id, route_group_id, progress, started_at, updated_at, finished_at)
                            VALUES (:id, :route_group_id, :progress, :started_at, :updated_at, :finished_at)
                        """),
                        {
                            "id": str(uuid.uuid4()),
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
            admin_id = str(uuid.uuid4())
            session.execute(
                text("""
                    INSERT INTO admin_info (admin_id, admin_name, default_cap, admin_phone, 
                                         admin_email, route_start_time, warehouse_location, created_at, updated_at)
                    VALUES (:id, :name, :cap, :phone, :email, :start_time, :warehouse, NOW(), NOW())
                """),
                {
                    "id": admin_id,
                    "name": fake.name(),
                    "cap": random.randint(20, 50),
                    "phone": fake.phone_number(),
                    "email": fake.email(),
                    "start_time": "08:00:00",
                    "warehouse": "330 Trillium Drive, Kitchener, ON",
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

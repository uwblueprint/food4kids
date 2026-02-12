"""
Test suite for database seeding script.

This test ensures:
1. The seeding script runs without errors
2. All major entity types are created properly
3. Schema changes cause test failures (by accessing specific fields)
"""

import os
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.admin import Admin
from app.models.driver import Driver
from app.models.driver_assignment import DriverAssignment
from app.models.driver_history import DriverHistory
from app.models.job import Job
from app.models.location import Location
from app.models.location_group import LocationGroup
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_group_membership import RouteGroupMembership
from app.models.route_stop import RouteStop
from app.models.system_settings import SystemSettings
from app.models.user import User


@pytest.mark.asyncio
async def test_seed_database_execution(test_session: AsyncSession) -> None:
    """
    Test that the seed database script runs successfully and creates all expected entities.

    This test also acts as a schema validation test:
    - If model fields are renamed/removed, the seeding script will fail with AttributeError
    - If new required fields are added without defaults, the seeding script will fail with validation errors
    - By accessing specific fields, we ensure they exist in the schema
    """

    # Mock environment variables for admin auth ID and test CSV path
    test_csv_path = os.path.join(
        os.path.dirname(__file__), "data", "test_locations.csv"
    )
    with patch.dict(
        os.environ,
        {
            "ADMIN_AUTH_ID": "test-admin-auth-id",
            "LOCATIONS_CSV_PATH": test_csv_path,
        },
    ):
        # Get the test database URL from environment (same as conftest.py uses)
        # Convert from async (postgresql+asyncpg://) to sync (postgresql://) for the seeding script
        async_db_url = os.getenv(
            "TEST_DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@db:5432/f4k_test",
        )
        # Convert async URL to sync URL for the synchronous seed script
        test_db_url = async_db_url.replace("postgresql+asyncpg://", "postgresql://")

        # Import and run the seeding script
        # Note: The seeding script uses synchronous SQLAlchemy, so we can't use our async test session
        # Instead, we'll verify the results in our async test session after seeding completes
        import app.seed_database as seed_module

        original_url = seed_module.DATABASE_URL
        seed_module.DATABASE_URL = test_db_url

        try:
            # Run the seeding script
            seed_module.main()
        finally:
            # Restore original URL
            seed_module.DATABASE_URL = original_url

    # Verify location groups were created
    location_groups = await test_session.execute(select(LocationGroup))
    location_groups_list = list(location_groups.scalars().all())
    assert len(location_groups_list) > 0, "No location groups were created"

    # Verify location group has expected fields (schema validation)
    first_group = location_groups_list[0]
    assert hasattr(first_group, "name"), "LocationGroup missing 'name' field"
    assert hasattr(first_group, "color"), "LocationGroup missing 'color' field"
    assert first_group.name is not None
    assert first_group.color is not None

    # Verify locations were created
    locations = await test_session.execute(select(Location))
    locations_list = list(locations.scalars().all())
    assert len(locations_list) > 0, "No locations were created"

    # Verify location has expected fields (schema validation)
    first_location = locations_list[0]
    assert hasattr(first_location, "contact_name"), (
        "Location missing 'contact_name' field"
    )
    assert hasattr(first_location, "address"), "Location missing 'address' field"
    assert hasattr(first_location, "phone_number"), (
        "Location missing 'phone_number' field"
    )
    assert hasattr(first_location, "latitude"), "Location missing 'latitude' field"
    assert hasattr(first_location, "longitude"), "Location missing 'longitude' field"
    assert hasattr(first_location, "halal"), "Location missing 'halal' field"
    assert hasattr(first_location, "num_boxes"), "Location missing 'num_boxes' field"
    assert first_location.contact_name is not None
    assert first_location.address is not None

    # Verify routes were created
    routes = await test_session.execute(select(Route))
    routes_list = list(routes.scalars().all())
    assert len(routes_list) > 0, "No routes were created"

    # Verify route has expected fields (schema validation)
    first_route = routes_list[0]
    assert hasattr(first_route, "name"), "Route missing 'name' field"
    assert hasattr(first_route, "length"), "Route missing 'length' field"
    assert first_route.name is not None
    assert first_route.length is not None

    # Verify route stops were created
    route_stops = await test_session.execute(select(RouteStop))
    route_stops_list = list(route_stops.scalars().all())
    assert len(route_stops_list) > 0, "No route stops were created"

    # Verify route stop has expected fields (schema validation)
    first_stop = route_stops_list[0]
    assert hasattr(first_stop, "route_id"), "RouteStop missing 'route_id' field"
    assert hasattr(first_stop, "location_id"), "RouteStop missing 'location_id' field"
    assert hasattr(first_stop, "stop_number"), "RouteStop missing 'stop_number' field"
    assert first_stop.stop_number >= 1

    # Verify users were created
    users = await test_session.execute(select(User))
    users_list = list(users.scalars().all())
    assert len(users_list) > 0, "No users were created"

    # Verify user has expected fields (schema validation)
    first_user = users_list[0]
    assert hasattr(first_user, "name"), "User missing 'name' field"
    assert hasattr(first_user, "email"), "User missing 'email' field"
    assert hasattr(first_user, "auth_id"), "User missing 'auth_id' field"
    assert first_user.name is not None
    assert first_user.email is not None

    # Verify drivers were created
    drivers = await test_session.execute(select(Driver))
    drivers_list = list(drivers.scalars().all())
    assert len(drivers_list) > 0, "No drivers were created"

    # Verify driver has expected fields (schema validation)
    first_driver = drivers_list[0]
    assert hasattr(first_driver, "user_id"), "Driver missing 'user_id' field"
    assert hasattr(first_driver, "phone"), "Driver missing 'phone' field"
    assert hasattr(first_driver, "address"), "Driver missing 'address' field"
    assert hasattr(first_driver, "license_plate"), (
        "Driver missing 'license_plate' field"
    )
    assert hasattr(first_driver, "car_make_model"), (
        "Driver missing 'car_make_model' field"
    )
    assert first_driver.phone is not None
    assert first_driver.license_plate is not None

    # Verify route groups were created
    route_groups = await test_session.execute(select(RouteGroup))
    route_groups_list = list(route_groups.scalars().all())
    assert len(route_groups_list) > 0, "No route groups were created"

    # Verify route group has expected fields (schema validation)
    first_route_group = route_groups_list[0]
    assert hasattr(first_route_group, "name"), "RouteGroup missing 'name' field"
    assert hasattr(first_route_group, "drive_date"), (
        "RouteGroup missing 'drive_date' field"
    )
    assert first_route_group.name is not None
    assert first_route_group.drive_date is not None

    # Verify route group memberships were created
    memberships = await test_session.execute(select(RouteGroupMembership))
    memberships_list = list(memberships.scalars().all())
    assert len(memberships_list) > 0, "No route group memberships were created"

    # Verify membership has expected fields (schema validation)
    first_membership = memberships_list[0]
    assert hasattr(first_membership, "route_group_id"), (
        "RouteGroupMembership missing 'route_group_id' field"
    )
    assert hasattr(first_membership, "route_id"), (
        "RouteGroupMembership missing 'route_id' field"
    )

    # Verify driver assignments were created
    assignments = await test_session.execute(select(DriverAssignment))
    assignments_list = list(assignments.scalars().all())
    assert len(assignments_list) > 0, "No driver assignments were created"

    # Verify driver assignment has expected fields (schema validation)
    first_assignment = assignments_list[0]
    assert hasattr(first_assignment, "driver_id"), (
        "DriverAssignment missing 'driver_id' field"
    )
    assert hasattr(first_assignment, "route_id"), (
        "DriverAssignment missing 'route_id' field"
    )
    assert hasattr(first_assignment, "route_group_id"), (
        "DriverAssignment missing 'route_group_id' field"
    )
    assert hasattr(first_assignment, "completed"), (
        "DriverAssignment missing 'completed' field"
    )

    # Verify driver history was created
    history = await test_session.execute(select(DriverHistory))
    history_list = list(history.scalars().all())
    assert len(history_list) > 0, "No driver history entries were created"

    # Verify driver history has expected fields (schema validation)
    first_history = history_list[0]
    assert hasattr(first_history, "driver_id"), (
        "DriverHistory missing 'driver_id' field"
    )
    assert hasattr(first_history, "year"), "DriverHistory missing 'year' field"
    assert hasattr(first_history, "km"), "DriverHistory missing 'km' field"
    assert first_history.year >= 2025
    assert first_history.km > 0

    # Verify jobs were created (optional, may be 0)
    jobs = await test_session.execute(select(Job))
    jobs_list = list(jobs.scalars().all())
    # Jobs may or may not be created depending on route groups, so we just check the schema if any exist
    if len(jobs_list) > 0:
        first_job = jobs_list[0]
        assert hasattr(first_job, "progress"), "Job missing 'progress' field"
        assert first_job.progress is not None

    # Verify system settings was created
    settings = await test_session.execute(select(SystemSettings))
    settings_list = list(settings.scalars().all())
    assert len(settings_list) > 0, "No system settings were created"

    # Verify system settings has expected fields (schema validation)
    first_settings = settings_list[0]
    assert hasattr(first_settings, "warehouse_location"), (
        "SystemSettings missing 'warehouse_location' field"
    )
    assert hasattr(first_settings, "warehouse_latitude"), (
        "SystemSettings missing 'warehouse_latitude' field"
    )
    assert hasattr(first_settings, "warehouse_longitude"), (
        "SystemSettings missing 'warehouse_longitude' field"
    )

    # Verify admin was created
    admins = await test_session.execute(select(Admin))
    admins_list = list(admins.scalars().all())
    assert len(admins_list) > 0, "No admin was created"

    # Verify admin has expected fields (schema validation)
    first_admin = admins_list[0]
    assert hasattr(first_admin, "user_id"), "Admin missing 'user_id' field"
    assert hasattr(first_admin, "admin_phone"), "Admin missing 'admin_phone' field"
    assert first_admin.admin_phone is not None

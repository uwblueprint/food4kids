"""
Test suite for the database seeding script.

These tests verify that the seeding script:
1. Executes successfully and populates every expected table
2. Creates the right number of rows for each entity
3. Produces data that satisfies business validation rules
4. Wires up foreign-key relationships consistently

Every test re-runs the synchronous ``seed_database.main()`` and verifies
against the async ``test_session`` fixture defined in ``conftest.py``. Tests
are marked ``slow`` because each seed run hits the database.
"""

import os
import re
from unittest.mock import patch

import phonenumbers
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

import app.seed_database as seed_module
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

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

TEST_CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "test_locations.csv")


def _run_seed_script() -> None:
    """Run the synchronous seed script against the test database.

    ``ADMIN_AUTH_ID`` is captured at module import time, so patching the env
    var after import is too late — patch the module attribute directly.
    ``LOCATIONS_CSV_PATH`` is read at runtime inside ``main()``, so an env
    patch is fine for it.
    """
    async_db_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@db:5432/f4k_test",
    )
    sync_db_url = async_db_url.replace("postgresql+asyncpg://", "postgresql://")

    with (
        patch.object(seed_module, "DATABASE_URL", sync_db_url),
        patch.object(seed_module, "ADMIN_AUTH_ID", "test-admin-auth-id"),
        patch.dict(os.environ, {"LOCATIONS_CSV_PATH": TEST_CSV_PATH}),
    ):
        seed_module.main()


@pytest.mark.slow
class TestSeedScriptExecution:
    """The seed script runs end-to-end and creates all expected entities."""

    @pytest.mark.asyncio
    async def test_all_entities_created_with_required_fields(
        self, test_session: AsyncSession
    ) -> None:
        """Smoke test: every model type is populated and exposes its schema fields.

        Doubles as schema validation — if a model field is renamed or
        removed, the ``hasattr`` checks here fail loudly.
        """
        _run_seed_script()

        location_groups = (
            await test_session.execute(select(LocationGroup))
        ).scalars().all()
        assert len(location_groups) > 0, "No location groups were created"
        first_group = location_groups[0]
        assert hasattr(first_group, "name")
        assert hasattr(first_group, "color")
        assert first_group.name is not None
        assert first_group.color is not None

        locations = (await test_session.execute(select(Location))).scalars().all()
        assert len(locations) > 0, "No locations were created"
        first_location = locations[0]
        for field in (
            "contact_name",
            "address",
            "phone_number",
            "latitude",
            "longitude",
            "halal",
            "num_boxes",
        ):
            assert hasattr(first_location, field), f"Location missing '{field}'"
        assert first_location.contact_name is not None
        assert first_location.address is not None

        routes = (await test_session.execute(select(Route))).scalars().all()
        assert len(routes) > 0, "No routes were created"
        first_route = routes[0]
        assert hasattr(first_route, "name")
        assert hasattr(first_route, "length")
        assert first_route.name is not None
        assert first_route.length is not None

        route_stops = (
            await test_session.execute(select(RouteStop))
        ).scalars().all()
        assert len(route_stops) > 0, "No route stops were created"
        first_stop = route_stops[0]
        for field in ("route_id", "location_id", "stop_number"):
            assert hasattr(first_stop, field), f"RouteStop missing '{field}'"
        assert first_stop.stop_number >= 1

        users = (await test_session.execute(select(User))).scalars().all()
        assert len(users) > 0, "No users were created"
        first_user = users[0]
        for field in ("name", "email", "auth_id"):
            assert hasattr(first_user, field), f"User missing '{field}'"
        assert first_user.name is not None
        assert first_user.email is not None

        drivers = (await test_session.execute(select(Driver))).scalars().all()
        assert len(drivers) > 0, "No drivers were created"
        first_driver = drivers[0]
        for field in (
            "user_id",
            "phone",
            "address",
            "license_plate",
            "car_make_model",
        ):
            assert hasattr(first_driver, field), f"Driver missing '{field}'"
        assert first_driver.phone is not None
        assert first_driver.license_plate is not None

        route_groups = (
            await test_session.execute(select(RouteGroup))
        ).scalars().all()
        assert len(route_groups) > 0, "No route groups were created"
        first_route_group = route_groups[0]
        assert hasattr(first_route_group, "name")
        assert hasattr(first_route_group, "drive_date")
        assert first_route_group.name is not None
        assert first_route_group.drive_date is not None

        memberships = (
            await test_session.execute(select(RouteGroupMembership))
        ).scalars().all()
        assert len(memberships) > 0, "No route group memberships were created"
        first_membership = memberships[0]
        assert hasattr(first_membership, "route_group_id")
        assert hasattr(first_membership, "route_id")

        assignments = (
            await test_session.execute(select(DriverAssignment))
        ).scalars().all()
        assert len(assignments) > 0, "No driver assignments were created"
        first_assignment = assignments[0]
        for field in ("driver_id", "route_id", "route_group_id"):
            assert hasattr(first_assignment, field), (
                f"DriverAssignment missing '{field}'"
            )

        history = (
            await test_session.execute(select(DriverHistory))
        ).scalars().all()
        assert len(history) > 0, "No driver history entries were created"
        first_history = history[0]
        for field in ("driver_id", "year", "month", "km"):
            assert hasattr(first_history, field), f"DriverHistory missing '{field}'"
        assert first_history.year >= 2025
        assert first_history.km > 0

        jobs = (await test_session.execute(select(Job))).scalars().all()
        if jobs:
            assert hasattr(jobs[0], "progress")
            assert jobs[0].progress is not None

        settings = (
            await test_session.execute(select(SystemSettings))
        ).scalars().all()
        assert len(settings) > 0, "No system settings were created"
        first_settings = settings[0]
        for field in (
            "warehouse_location",
            "warehouse_latitude",
            "warehouse_longitude",
        ):
            assert hasattr(first_settings, field), f"SystemSettings missing '{field}'"

        admins = (await test_session.execute(select(Admin))).scalars().all()
        assert len(admins) > 0, "No admin was created"
        assert hasattr(admins[0], "user_id")
        assert hasattr(admins[0], "admin_phone")
        assert admins[0].admin_phone is not None


@pytest.mark.slow
class TestDataCounts:
    """Counts of seeded entities match the script's declared constants."""

    @pytest.mark.asyncio
    async def test_location_group_count_matches_schedule(
        self, test_session: AsyncSession
    ) -> None:
        _run_seed_script()

        groups = (
            await test_session.execute(select(LocationGroup))
        ).scalars().all()
        assert len(groups) == len(seed_module.LOCATION_GROUP_SCHEDULE), (
            "Location group count should match LOCATION_GROUP_SCHEDULE keys"
        )

    @pytest.mark.asyncio
    async def test_driver_count_meets_minimum(
        self, test_session: AsyncSession
    ) -> None:
        _run_seed_script()

        drivers = (await test_session.execute(select(Driver))).scalars().all()
        routes = (await test_session.execute(select(Route))).scalars().all()
        expected_minimum = min(seed_module.MIN_DRIVERS, len(routes))
        assert len(drivers) >= expected_minimum, (
            f"Expected at least {expected_minimum} drivers, got {len(drivers)}"
        )


@pytest.mark.slow
class TestDataValidation:
    """Seeded data satisfies business validation rules."""

    @pytest.mark.asyncio
    async def test_phone_numbers_are_e164(self, test_session: AsyncSession) -> None:
        _run_seed_script()

        drivers = (await test_session.execute(select(Driver))).scalars().all()
        for driver in drivers:
            assert driver.phone.startswith("+"), (
                f"Driver phone {driver.phone} should be E.164"
            )
            assert phonenumbers.is_valid_number(
                phonenumbers.parse(driver.phone, None)
            ), f"Driver phone {driver.phone} should parse as valid"

        locations = (await test_session.execute(select(Location))).scalars().all()
        for location in locations:
            assert location.phone_number.startswith("+"), (
                f"Location phone {location.phone_number} should be E.164"
            )
            assert phonenumbers.is_valid_number(
                phonenumbers.parse(location.phone_number, None)
            ), f"Location phone {location.phone_number} should parse as valid"

        admins = (await test_session.execute(select(Admin))).scalars().all()
        for admin in admins:
            assert admin.admin_phone.startswith("+"), (
                f"Admin phone {admin.admin_phone} should be E.164"
            )
            assert phonenumbers.is_valid_number(
                phonenumbers.parse(admin.admin_phone, None)
            ), f"Admin phone {admin.admin_phone} should parse as valid"

    @pytest.mark.asyncio
    async def test_email_addresses_match_pattern(
        self, test_session: AsyncSession
    ) -> None:
        _run_seed_script()

        users = (await test_session.execute(select(User))).scalars().all()
        assert users, "Expected at least one user"
        for user in users:
            assert "@" in user.email, f"User email {user.email} missing '@'"
            assert EMAIL_PATTERN.match(user.email), (
                f"User email {user.email} should match email pattern"
            )

    @pytest.mark.asyncio
    async def test_route_lengths_non_negative(
        self, test_session: AsyncSession
    ) -> None:
        _run_seed_script()

        routes = (await test_session.execute(select(Route))).scalars().all()
        for route in routes:
            assert route.length >= 0, (
                f"Route {route.route_id} length {route.length} should be non-negative"
            )

    @pytest.mark.asyncio
    async def test_driver_history_years_in_range(
        self, test_session: AsyncSession
    ) -> None:
        _run_seed_script()

        history = (
            await test_session.execute(select(DriverHistory))
        ).scalars().all()
        for entry in history:
            assert 2025 <= entry.year <= 2100, (
                f"DriverHistory year {entry.year} should be in [2025, 2100]"
            )

    @pytest.mark.asyncio
    async def test_timestamps_populated(self, test_session: AsyncSession) -> None:
        _run_seed_script()

        for model in (Location, Driver, Route):
            rows = (await test_session.execute(select(model).limit(5))).scalars().all()
            for row in rows:
                assert row.created_at is not None, (
                    f"{model.__name__} {row} should have created_at"
                )
                assert row.updated_at is not None, (
                    f"{model.__name__} {row} should have updated_at"
                )


@pytest.mark.slow
class TestRelationshipIntegrity:
    """Foreign keys point at rows that actually exist."""

    @pytest.mark.asyncio
    async def test_route_stops_are_sequential_and_link_to_locations(
        self, test_session: AsyncSession
    ) -> None:
        _run_seed_script()

        routes = (await test_session.execute(select(Route))).scalars().all()
        assert routes, "Need at least one route to test stops"

        for route in routes:
            stops = (
                await test_session.execute(
                    select(RouteStop)
                    .where(RouteStop.route_id == route.route_id)
                    .order_by(RouteStop.stop_number)
                )
            ).scalars().all()
            assert stops, f"Route {route.route_id} should have stops"

            stop_numbers = [stop.stop_number for stop in stops]
            assert stop_numbers == list(range(1, len(stops) + 1)), (
                f"Route {route.route_id} stops should be 1..{len(stops)}, "
                f"got {stop_numbers}"
            )

            for stop in stops:
                location = (
                    await test_session.execute(
                        select(Location).where(
                            Location.location_id == stop.location_id
                        )
                    )
                ).scalars().first()
                assert location is not None, (
                    f"RouteStop {stop.route_stop_id} references missing location "
                    f"{stop.location_id}"
                )

    @pytest.mark.asyncio
    async def test_memberships_reference_valid_routes(
        self, test_session: AsyncSession
    ) -> None:
        _run_seed_script()

        memberships = (
            await test_session.execute(select(RouteGroupMembership))
        ).scalars().all()
        assert memberships, "No memberships seeded"

        for membership in memberships:
            route = (
                await test_session.execute(
                    select(Route).where(Route.route_id == membership.route_id)
                )
            ).scalars().first()
            assert route is not None, (
                f"Membership references missing route {membership.route_id}"
            )

            route_group = (
                await test_session.execute(
                    select(RouteGroup).where(
                        RouteGroup.route_group_id == membership.route_group_id
                    )
                )
            ).scalars().first()
            assert route_group is not None, (
                f"Membership references missing route group "
                f"{membership.route_group_id}"
            )

    @pytest.mark.asyncio
    async def test_assignments_reference_valid_drivers_and_routes(
        self, test_session: AsyncSession
    ) -> None:
        _run_seed_script()

        assignments = (
            await test_session.execute(select(DriverAssignment))
        ).scalars().all()
        if not assignments:
            pytest.skip("Seed did not create driver assignments")

        for assignment in assignments:
            driver = (
                await test_session.execute(
                    select(Driver).where(Driver.driver_id == assignment.driver_id)
                )
            ).scalars().first()
            assert driver is not None, (
                f"Assignment references missing driver {assignment.driver_id}"
            )

            route = (
                await test_session.execute(
                    select(Route).where(Route.route_id == assignment.route_id)
                )
            ).scalars().first()
            assert route is not None, (
                f"Assignment references missing route {assignment.route_id}"
            )

    @pytest.mark.asyncio
    async def test_history_references_valid_drivers(
        self, test_session: AsyncSession
    ) -> None:
        _run_seed_script()

        history = (
            await test_session.execute(select(DriverHistory))
        ).scalars().all()
        assert history, "No driver history seeded"

        for entry in history:
            driver = (
                await test_session.execute(
                    select(Driver).where(Driver.driver_id == entry.driver_id)
                )
            ).scalars().first()
            assert driver is not None, (
                f"DriverHistory entry references missing driver {entry.driver_id}"
            )

    @pytest.mark.asyncio
    async def test_jobs_reference_valid_route_groups(
        self, test_session: AsyncSession
    ) -> None:
        _run_seed_script()

        jobs = (await test_session.execute(select(Job))).scalars().all()
        if not jobs:
            pytest.skip("Seed did not create jobs")

        for job in jobs:
            if job.route_group_id is None:
                continue
            route_group = (
                await test_session.execute(
                    select(RouteGroup).where(
                        RouteGroup.route_group_id == job.route_group_id
                    )
                )
            ).scalars().first()
            assert route_group is not None, (
                f"Job {job.job_id} references missing route group "
                f"{job.route_group_id}"
            )

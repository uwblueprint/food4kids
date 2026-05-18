"""
Test suite for the database seeding script.

These tests verify that the seeding script:
1. Executes successfully and populates every expected table
2. Creates the right number of rows for each entity
3. Produces data that satisfies business validation rules
4. Wires up route-stop sequence invariants correctly

Every test re-runs the synchronous ``seed_database.main()`` and verifies
against the async ``test_session`` fixture from ``conftest.py``. Tests are
marked ``slow`` because each one pays a full seed cycle.
"""

import os
import re
from datetime import datetime, timedelta
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

# Driver history covers MONTHS_PAST..MONTHS_FUTURE around today.
_MIN_HISTORY_YEAR = (datetime.now() - timedelta(days=seed_module.MONTHS_PAST * 31)).year
_MAX_HISTORY_YEAR = (
    datetime.now() + timedelta(days=seed_module.MONTHS_FUTURE * 31)
).year


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


@pytest.fixture(autouse=True)
def _seed_database(test_db_engine) -> None:  # noqa: ARG001
    """Run the seed script once per test, after the shared engine fixture has
    reset tables. The ``test_db_engine`` parameter establishes the fixture
    dependency so the drop/create cycle completes before seeding.
    """
    _run_seed_script()


# (model, [required_fields]) — covers every entity the seed populates.
_ENTITY_FIELDS: list[tuple[type, list[str]]] = [
    (LocationGroup, ["name", "color"]),
    (
        Location,
        [
            "contact_name",
            "address",
            "phone_number",
            "latitude",
            "longitude",
            "halal",
            "num_boxes",
        ],
    ),
    (Route, ["name", "length"]),
    (RouteStop, ["route_id", "location_id", "stop_number"]),
    (User, ["name", "email", "auth_id"]),
    (
        Driver,
        ["user_id", "phone", "address", "license_plate", "car_make_model"],
    ),
    (RouteGroup, ["name", "drive_date"]),
    (RouteGroupMembership, ["route_group_id", "route_id"]),
    (DriverAssignment, ["driver_id", "route_id", "route_group_id"]),
    (DriverHistory, ["driver_id", "year", "month", "km"]),
    (Job, ["route_group_id", "progress", "started_at"]),
    (
        SystemSettings,
        ["warehouse_location", "warehouse_latitude", "warehouse_longitude"],
    ),
    (Admin, ["user_id", "admin_phone"]),
]


@pytest.mark.slow
class TestSeedScriptExecution:
    """The seed script runs end-to-end and creates all expected entities."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "model,required_fields",
        _ENTITY_FIELDS,
        ids=[m.__name__ for m, _ in _ENTITY_FIELDS],
    )
    async def test_entity_populated_with_required_fields(
        self,
        test_session: AsyncSession,
        model: type,
        required_fields: list[str],
    ) -> None:
        rows = (await test_session.execute(select(model))).scalars().all()
        assert len(rows) > 0, f"No {model.__name__} rows were created"

        first = rows[0]
        for field in required_fields:
            assert hasattr(first, field), f"{model.__name__} missing '{field}'"
            assert getattr(first, field) is not None, (
                f"{model.__name__}.{field} should not be None"
            )


@pytest.mark.slow
class TestDataCounts:
    """Counts of seeded entities match the script's declared constants."""

    @pytest.mark.asyncio
    async def test_location_group_count_matches_schedule(
        self, test_session: AsyncSession
    ) -> None:
        groups = (await test_session.execute(select(LocationGroup))).scalars().all()
        assert len(groups) == len(seed_module.LOCATION_GROUP_SCHEDULE), (
            "Location group count should match LOCATION_GROUP_SCHEDULE keys"
        )

    @pytest.mark.asyncio
    async def test_driver_count_meets_minimum(self, test_session: AsyncSession) -> None:
        # Seed uses `max(routes_created, MIN_DRIVERS)`, so the lower bound
        # is unconditionally MIN_DRIVERS.
        drivers = (await test_session.execute(select(Driver))).scalars().all()
        assert len(drivers) >= seed_module.MIN_DRIVERS, (
            f"Expected at least {seed_module.MIN_DRIVERS} drivers, got {len(drivers)}"
        )


@pytest.mark.slow
class TestDataValidation:
    """Seeded data satisfies business validation rules."""

    @pytest.mark.asyncio
    async def test_phone_numbers_are_e164(self, test_session: AsyncSession) -> None:
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
        users = (await test_session.execute(select(User))).scalars().all()
        assert users, "Expected at least one user"
        for user in users:
            assert EMAIL_PATTERN.match(user.email), (
                f"User email {user.email} should match email pattern"
            )

    @pytest.mark.asyncio
    async def test_route_lengths_non_negative(self, test_session: AsyncSession) -> None:
        routes = (await test_session.execute(select(Route))).scalars().all()
        for route in routes:
            assert route.length >= 0, (
                f"Route {route.route_id} length {route.length} should be non-negative"
            )

    @pytest.mark.asyncio
    async def test_driver_history_years_in_range(
        self, test_session: AsyncSession
    ) -> None:
        history = (await test_session.execute(select(DriverHistory))).scalars().all()
        assert history, "No driver history seeded"
        for entry in history:
            assert _MIN_HISTORY_YEAR <= entry.year <= _MAX_HISTORY_YEAR, (
                f"DriverHistory year {entry.year} should be in "
                f"[{_MIN_HISTORY_YEAR}, {_MAX_HISTORY_YEAR}]"
            )

    @pytest.mark.asyncio
    async def test_timestamps_populated(self, test_session: AsyncSession) -> None:
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
class TestRouteStopSequence:
    """Route stops form a 1..N sequence — a semantic invariant the DB schema
    does not enforce. (Pure FK existence is covered by Postgres itself.)"""

    @pytest.mark.asyncio
    async def test_route_stops_are_sequential(self, test_session: AsyncSession) -> None:
        routes = (await test_session.execute(select(Route))).scalars().all()
        assert routes, "Need at least one route to test stops"

        for route in routes:
            stops = (
                (
                    await test_session.execute(
                        select(RouteStop)
                        .where(RouteStop.route_id == route.route_id)
                        .order_by(RouteStop.stop_number)
                    )
                )
                .scalars()
                .all()
            )
            assert stops, f"Route {route.route_id} should have stops"

            stop_numbers = [stop.stop_number for stop in stops]
            assert stop_numbers == list(range(1, len(stops) + 1)), (
                f"Route {route.route_id} stops should be 1..{len(stops)}, "
                f"got {stop_numbers}"
            )

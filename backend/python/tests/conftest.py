"""
Global test configuration and fixtures for the Food4Kids application.
"""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

from app import create_app
from app.models import get_session

# Set test environment
os.environ["APP_ENV"] = "testing"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db_engine() -> AsyncGenerator[Any, None]:
    """Create a test database engine using PostgreSQL for compatibility with ARRAY types."""
    import os

    # Use PostgreSQL for testing to support ARRAY types
    database_url = os.getenv(
        "TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/f4k"
    )

    engine = create_async_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
    )

    # Create all tables
    async with engine.begin() as conn:
        # Import models to register them with SQLModel
        # Import in dependency order to avoid relationship resolution issues
        from app.models.driver import Driver  # noqa: F401

        # Import driver assignment model
        from app.models.driver_assignment import DriverAssignment  # noqa: F401
        from app.models.location import Location  # noqa: F401
        from app.models.location_group import LocationGroup  # noqa: F401
        from app.models.route import Route  # noqa: F401

        # Import relationship models after their dependencies
        # RouteGroup must be imported before RouteGroupMembership to avoid circular dependency
        from app.models.route_group import RouteGroup  # noqa: F401
        from app.models.route_group_membership import RouteGroupMembership  # noqa: F401
        from app.models.route_stop import RouteStop  # noqa: F401

        # Drop all tables first to ensure clean state
        await conn.run_sync(SQLModel.metadata.drop_all)
        # Create tables
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Cleanup - drop tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_db_engine: Any) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with automatic rollback."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async_session = async_sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Start a transaction
        transaction = await session.begin()

        try:
            yield session
        finally:
            # Rollback the transaction to clean up
            import contextlib

            with contextlib.suppress(Exception):
                await transaction.rollback()


@pytest.fixture(scope="function")
def client(test_session: AsyncSession) -> Generator[TestClient, None, None]:
    """Create a test client with database session override."""
    app = create_app()

    # Override the database session dependency
    def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async def _get_session() -> AsyncGenerator[AsyncSession, None]:
            yield test_session

        return _get_session()

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture(scope="function")
async def async_client(
    test_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with database session override."""
    app = create_app()

    # Override the database session dependency
    def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async def _get_session() -> AsyncGenerator[AsyncSession, None]:
            yield test_session

        return _get_session()

    app.dependency_overrides[get_session] = override_get_session

    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# Authentication fixtures
@pytest.fixture
def mock_firebase_auth(mocker: Any) -> Any:
    """Mock Firebase authentication for testing."""
    mock_user = mocker.MagicMock()
    mock_user.email = "test@example.com"
    mock_user.uid = "test-uid-123"

    # Mock Firebase admin auth
    mock_get_user = mocker.patch("firebase_admin.auth.get_user", return_value=mock_user)
    mock_verify_token = mocker.patch(
        "firebase_admin.auth.verify_id_token",
        return_value={"uid": "test-uid-123", "email": "test@example.com"},
    )

    return {
        "get_user": mock_get_user,
        "verify_token": mock_verify_token,
        "user": mock_user,
    }


@pytest.fixture
def mock_firebase_admin_auth(mocker: Any) -> Any:
    """Mock firebase_admin.auth functions."""
    mock_auth = mocker.patch("firebase_admin.auth", autospec=True)
    mock_auth.verify_id_token.return_value = {
        "uid": "mock_firebase_uid",
        "email": "test@example.com",
        "role": "User",
    }
    mock_auth.get_user.return_value.email = "test@example.com"
    mock_auth.get_user_by_email.return_value.uid = "mock_firebase_uid"
    mock_auth.create_user.return_value.uid = "mock_firebase_uid"
    return mock_auth


@pytest.fixture
def mock_auth_service(mocker: Any) -> Any:
    """Mock the auth service for testing."""
    mock_service = mocker.patch("app.services.implementations.auth_service.AuthService")
    mock_service.return_value.is_authorized_by_role.return_value = True
    mock_service.return_value.is_authorized_by_user_id.return_value = True
    mock_service.return_value.is_authorized_by_email.return_value = True
    return mock_service


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Provide authentication headers for testing."""
    return {"Authorization": "Bearer test-token"}


# Test data fixtures
@pytest.fixture
def sample_driver_data() -> dict[str, Any]:
    """Sample driver data for testing."""
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+12125551234",  # Valid international format
        "address": "123 Main St, City, State 12345",
        "license_plate": "ABC123",
        "car_make_model": "Toyota Camry",
        "auth_id": "test-auth-id-123",
    }


@pytest.fixture
def sample_location_group_data() -> dict[str, Any]:
    """Sample location group data for testing."""
    return {
        "name": "Downtown Schools",
        "color": "#FF5733",
        "notes": "Schools in downtown area",
    }


@pytest.fixture
def sample_location_data() -> dict[str, Any]:
    """Sample location data for testing."""
    return {
        "school_name": "Central Elementary",
        "contact_name": "Jane Smith",
        "address": "123 Main St, City, State 12345",
        "phone_number": "(555) 123-4567",
        "longitude": -122.4194,
        "latitude": 37.7749,
        "halal": False,
        "dietary_restrictions": "No nuts",
        "num_children": 150,
        "num_boxes": 25,
        "notes": "Main entrance on Main St",
    }


@pytest.fixture
def sample_route_data() -> dict[str, Any]:
    """Sample route data for testing."""
    return {
        "name": "Downtown Route",
        "notes": "Main downtown delivery route",
        "length": 15.5,
    }


@pytest_asyncio.fixture
async def test_driver(
    test_session: AsyncSession, sample_driver_data: dict[str, Any]
) -> Any:
    """Create a test driver in the database."""
    from app.models.user import User
    from app.models.driver import Driver

    user = User(
        name=sample_driver_data["name"],
        email=sample_driver_data['email'],
        auth_id=sample_driver_data['auth_id'],
    )
    test_session.add(user)
    driver = Driver(
        user_id=user.user_id,
        phone=sample_driver_data["phone"],
        address=sample_driver_data["address"],
        license_plate=sample_driver_data["license_plate"],
        car_make_model=sample_driver_data["car_make_model"],
    )
    test_session.add(driver)
    await test_session.commit()
    await test_session.refresh(driver)
    return driver


@pytest_asyncio.fixture
async def test_route(
    test_session: AsyncSession, sample_route_data: dict[str, Any]
) -> Any:
    """Create a test route in the database."""
    from app.models.route import Route

    route = Route(**sample_route_data)
    test_session.add(route)
    await test_session.commit()
    await test_session.refresh(route)
    return route

import os
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel, create_engine

# Database engines
engine: Engine | None = None
async_engine: AsyncEngine | None = None
async_session_maker_instance: async_sessionmaker[AsyncSession] | None = None


def get_database_url() -> str:
    """Get database URL based on environment"""
    if os.getenv("APP_ENV") == "production":
        return os.getenv("DATABASE_URL", "").replace(
            "postgresql://", "postgresql+asyncpg://"
        )
    else:
        return "postgresql+asyncpg://{username}:{password}@{host}:5432/{db}".format(
            username=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("DB_HOST"),
            db=(
                os.getenv("POSTGRES_DB_TEST")
                if os.getenv("APP_ENV") == "testing"
                else os.getenv("POSTGRES_DB_DEV")
            ),
        )


def init_database() -> None:
    """Initialize database engines and session makers"""
    global engine, async_engine, async_session_maker_instance

    database_url = get_database_url()
    sync_database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    # Set echo based on environment
    app_env = os.getenv("APP_ENV")
    echo_sql = app_env in ("development", "testing")

    # Synchronous engine for migrations
    engine = create_engine(sync_database_url, echo=echo_sql)

    # Asynchronous engine for application
    async_engine = create_async_engine(database_url, echo=echo_sql)

    # Async session maker
    async_session_maker_instance = async_sessionmaker(
        async_engine, expire_on_commit=False
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    if async_session_maker_instance is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    async with async_session_maker_instance() as session:
        try:
            yield session
        finally:
            await session.close()


def create_db_and_tables() -> None:
    """Create database tables - for testing/development"""
    if engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    SQLModel.metadata.create_all(engine)


def init_app(_app: Any | None = None) -> None:
    """Initialize database for the application"""
    from .admin import Admin  # noqa: F401
    from .driver import Driver  # noqa: F401
    from .driver_assignment import DriverAssignment  # noqa: F401
    from .driver_history import DriverHistory  # noqa: F401
    from .entity import Entity  # noqa: F401
    from .job import Job  # noqa: F401
    from .location import Location  # noqa: F401
    from .location_group import LocationGroup  # noqa: F401
    from .route_stop import RouteStop  # noqa: F401
    from .route import Route  # noqa: F401

    from .route_group import RouteGroup  # noqa: F401
    from .route_group_membership import RouteGroupMembership  # noqa: F401
    from .simple_entity import SimpleEntity  # noqa: F401

    init_database()

    # Create tables if in testing mode
    if os.getenv("APP_ENV") == "testing":
        create_db_and_tables()

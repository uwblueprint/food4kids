import os
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import Engine, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel, create_engine

from app.config import settings

# Database engines
engine: Engine | None = None
async_engine: AsyncEngine | None = None
async_session_maker_instance: async_sessionmaker[AsyncSession] | None = None


def get_database_url() -> str:
    """Get database URL based on configuration settings"""
    # 1. Use the unified URL if provided (Cloud Run secret mount)
    if settings.database_url:
        url_obj = make_url(settings.database_url)
        return url_obj.set(drivername="postgresql+asyncpg").render_as_string(
            hide_password=False
        )

    # 2. Fallback for local development (safe for localhost, no forced SSL)
    base_url = f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}@{settings.db_host}:5432"

    if settings.is_testing:
        return f"{base_url}/{settings.postgres_db_test}"
    else:
        return f"{base_url}/{settings.postgres_db_dev}?sslmode=require"


def init_database() -> None:
    """Initialize database engines and session makers"""
    global engine, async_engine, async_session_maker_instance

    database_url = get_database_url()

    # 1. Check if we're pointing to Neon
    is_neon = "neon.tech" in database_url

    # 2. Synchronous engine (Alembic/psycopg2) loves the string parameter
    sync_database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    if is_neon and "sslmode" not in sync_database_url:
        sync_database_url += (
            "?sslmode=require" if "?" not in sync_database_url else "&sslmode=require"
        )

    # Set echo based on environment
    app_env = os.getenv("APP_ENV")
    echo_sql = app_env in ("development", "testing")

    engine = create_engine(sync_database_url, echo=echo_sql)

    # asyncpg doesn't accept libpq-style query params (sslmode, channel_binding
    # from Neon's connection string) as connect() kwargs - it wants `ssl=`
    # instead - so strip them from the URL and pass SSL via connect_args.
    async_url = make_url(database_url)
    connect_args: dict[str, Any] = {}
    if "sslmode" in async_url.query:
        query = dict(async_url.query)
        connect_args["ssl"] = query.pop("sslmode")
        query.pop("channel_binding", None)
        async_url = async_url.set(query=query)
    elif is_neon:
        connect_args["ssl"] = "require"

    # Asynchronous engine for application
    async_engine = create_async_engine(
        async_url, echo=echo_sql, connect_args=connect_args
    )

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
    # Import models to register them with SQLModel
    from .admin import Admin  # noqa: F401
    from .announcement import Announcement  # noqa: F401
    from .announcement_last_read import AnnouncementLastRead  # noqa: F401
    from .driver import Driver  # noqa: F401
    from .driver_history import DriverHistory  # noqa: F401
    from .job import Job  # noqa: F401
    from .location import Location  # noqa: F401
    from .location_group import LocationGroup  # noqa: F401
    from .note import Note  # noqa: F401
    from .note_chain import NoteChain  # noqa: F401
    from .route import Route  # noqa: F401
    from .route_group import RouteGroup  # noqa: F401
    from .route_snapshot import RouteSnapshot  # noqa: F401
    from .route_stop import RouteStop  # noqa: F401
    from .route_stop_snapshot import RouteStopSnapshot  # noqa: F401
    from .system_settings import SystemSettings  # noqa: F401
    from .user import User  # noqa: F401
    from .user_invite import UserInvite  # noqa: F401

    init_database()

    # Create tables if in testing mode
    if os.getenv("APP_ENV") == "testing":
        create_db_and_tables()

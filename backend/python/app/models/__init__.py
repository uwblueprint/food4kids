import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

# Database engines
engine = None
async_engine = None
async_session_maker = None


def get_database_url() -> str:
    """Get database URL based on environment"""
    if os.getenv("APP_ENV") == "production":
        return os.getenv("DATABASE_URL", "").replace("postgresql://", "postgresql+asyncpg://")
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


def init_database():
    """Initialize database engines and session makers"""
    global engine, async_engine, async_session_maker
    
    database_url = get_database_url()
    sync_database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    # Synchronous engine for migrations
    engine = create_engine(sync_database_url, echo=True)
    
    # Asynchronous engine for application
    async_engine = create_async_engine(database_url, echo=True)
    
    # Async session maker
    async_session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


def create_db_and_tables():
    """Create database tables - for testing/development"""
    SQLModel.metadata.create_all(engine)


def init_app(app=None):
    """Initialize database for the application"""
    # Import models to register them with SQLModel
    from .entity import Entity
    from .simple_entity import SimpleEntity
    from .user import User
    
    init_database()
    
    # Create tables if in testing mode
    if os.getenv("APP_ENV") == "testing":
        create_db_and_tables()

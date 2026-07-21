from __future__ import with_statement

import logging
import os
import sys
from logging.config import fileConfig
from typing import Any
import json

# Add the project root to Python path to ensure app module can be imported
# This handles both running from /app and /app/migrations
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlmodel import SQLModel
from alembic import context

# Import all models to ensure they're registered with SQLModel
from app.models.admin import Admin
from app.models.announcement import Announcement
from app.models.driver import Driver
from app.models.driver_history import DriverHistory
from app.models.job import Job
from app.models.location import Location
from app.models.location_group import LocationGroup
from app.models.note import Note
from app.models.note_chain import NoteChain
from app.models.note_chain_read import NoteChainReadModel
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_snapshot import RouteSnapshot
from app.models.route_stop import RouteStop
from app.models.route_stop_snapshot import RouteStopSnapshot
from app.models.system_settings import SystemSettings
from app.models.user import User
from app.models.user_invite import UserInvite

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name:
    fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

def get_database_url() -> str:
    # Check if running on GCloud (secrets path only exists then, not in local dev)
    secret_path = "/secrets/config.json"
    print(f"--- DEBUG: Checking for secret file at {secret_path}. Exists: {os.path.exists(secret_path)} ---")
    
    if os.path.exists(secret_path):
        try:
            with open(secret_path, "r") as f:
                secret_data = json.load(f)
            
            print(f"--- DEBUG: Successfully loaded JSON. Keys found: {list(secret_data.keys())} ---")
                
            # Try using the direct full connection string first
            if "database_url" in secret_data:
                url = secret_data["database_url"]
                # Convert driver for Alembic/psycopg2 (it needs postgresql:// instead of postgresql+asyncpg://)
                if url.startswith("postgresql+asyncpg://"):
                    url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
                elif url.startswith("postgres://"):
                    url = url.replace("postgres://", "postgresql://", 1)
                
                # Double-check SSL parameters are preserved
                if "sslmode" not in url:
                    url += "?sslmode=require" if "?" not in url else "&sslmode=require"
                return url
                
            # Fallback to structural builder if direct URL key is absent
            username = secret_data.get("POSTGRES_USER", os.getenv("POSTGRES_USER"))
            password = secret_data.get("POSTGRES_PASSWORD") 
            host = secret_data.get("DB_HOST", os.getenv("DB_HOST"))
            db = secret_data.get("POSTGRES_DB_DEV", os.getenv("POSTGRES_DB_DEV"))
            
            print(f"--- DEBUG: Extracted user={username}, host={host}, db={db}, has_password=bool(password) ---")
            
            base_url = f"postgresql://{username}:{password}@{host}:5432/{db}"
            if "sslmode" not in base_url:
                base_url += "?sslmode=require"
                
            return base_url
        except Exception as e:
            print(f"--- DEBUG: Exception hit while reading secret JSON: {e} ---")
    # Else run normal local logic
    if os.getenv("APP_ENV") == "production":
        url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")
        # Ensure production URL has sslmode if not already present
        if "sslmode" not in url:
            url += "?sslmode=require" if "?" not in url else "&sslmode=require"
        return url
    else:
        # 1. Dynamically build the base local connection URL first
        base_url = "postgresql://{username}:{password}@{host}:5432/{db}".format(
            username=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("DB_HOST"),
            db=(
                os.getenv("POSTGRES_DB_TEST")
                if os.getenv("APP_ENV") == "testing"
                else os.getenv("POSTGRES_DB_DEV")
            ),
        )
        
        # 2. Only append sslmode if DB_HOST points to Neon (e.g. on Cloud Run)
        db_host = os.getenv("DB_HOST", "")
        if "neon.tech" in db_host:
            base_url += "?sslmode=require"
            
        return base_url

config.set_main_option("sqlalchemy.url", get_database_url())
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context: Any, revision: Any, directives: Any) -> None:
        if getattr(config.cmd_opts, "autogenerate", False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info("No changes in schema detected.")

    from sqlalchemy import create_engine
    
    connectable = create_engine(get_database_url())

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

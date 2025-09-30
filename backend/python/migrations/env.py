from __future__ import with_statement

import logging
import os
import sys
from logging.config import fileConfig

# Add the project root to Python path to ensure app module can be imported
# This handles both running from /app and /app/migrations
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlmodel import SQLModel
from alembic import context

# Import all models to ensure they're registered with SQLModel
from app.models.user import User
from app.models.entity import Entity
from app.models.simple_entity import SimpleEntity

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

# Set the database URL from environment
def get_database_url():
    if os.getenv("APP_ENV") == "production":
        return os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")
    else:
        return "postgresql://{username}:{password}@{host}:5432/{db}".format(
            username=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("DB_HOST"),
            db=(
                os.getenv("POSTGRES_DB_TEST")
                if os.getenv("APP_ENV") == "testing"
                else os.getenv("POSTGRES_DB_DEV")
            ),
        )

config.set_main_option("sqlalchemy.url", get_database_url())
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
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


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
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

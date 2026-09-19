"""The one place the database URL is assembled.

The app, Alembic and the seed script all need it, and three separate copies is
how they drift apart. Everything comes from ``Settings``: on Cloud Run the
config arrives as a mounted secrets file, so anything read through
``os.getenv`` is invisible there even when it is present in the secret.
"""

from typing import Final, Literal

from sqlalchemy import URL, make_url

from app.config import Environment, settings

Driver = Literal["postgresql+asyncpg", "postgresql"]
ASYNC_DRIVER: Final[Driver] = "postgresql+asyncpg"
SYNC_DRIVER: Final[Driver] = "postgresql"


def get_database_url(driver: Driver = ASYNC_DRIVER) -> str:
    """Build the database URL for ``driver``.

    Raises if the credentials it needs are missing, rather than handing back a
    URL with "None" where the host should be and failing at connect time.
    """
    if settings.environment is Environment.PRODUCTION:
        # Settings refuses to start in production without DATABASE_URL.
        return (
            make_url(settings.database_url)
            .set(drivername=driver)
            .render_as_string(hide_password=False)
        )

    is_testing = settings.environment is Environment.TESTING
    database = settings.postgres_db_test if is_testing else settings.postgres_db_dev
    database_var = "POSTGRES_DB_TEST" if is_testing else "POSTGRES_DB_DEV"

    missing = sorted(
        name
        for name, value in (
            ("POSTGRES_USER", settings.postgres_user),
            ("POSTGRES_PASSWORD", settings.postgres_password),
            ("DB_HOST", settings.db_host),
            (database_var, database),
        )
        if not value
    )
    if missing:
        raise RuntimeError(
            f"Cannot build a database URL for {settings.environment}: "
            f"{', '.join(missing)} not set."
        )

    # URL.create escapes the password, which f-string interpolation does not.
    return URL.create(
        drivername=driver,
        username=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.db_host,
        port=5432,
        database=database,
    ).render_as_string(hide_password=False)

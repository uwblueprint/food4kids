"""``init_database()`` builds both engines from the shared URL builder.

The builder's output is consumed twice: verbatim by the sync engine, and
after sslmode-stripping by the async one. These pin that both ends still
line up, without a database: neither engine connects at construction.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from sqlalchemy import URL

from app import models
from app.config import Environment, settings


@pytest.fixture(autouse=True)
def isolated_engines(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Start from no engines and put back whatever the suite had afterwards."""
    monkeypatch.setattr(models, "engine", None)
    monkeypatch.setattr(models, "async_engine", None)
    monkeypatch.setattr(models, "async_session_maker_instance", None)
    yield
    if models.engine is not None:
        models.engine.dispose()
    if models.async_engine is not None:
        models.async_engine.sync_engine.dispose()


@pytest.fixture
def async_engine_kwargs(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Record the kwargs the async engine is built with; connect_args are not
    readable off the finished engine."""
    recorded: dict[str, Any] = {}
    real = models.create_async_engine

    def spy(url: URL, **kwargs: Any) -> Any:
        recorded.update(kwargs)
        return real(url, **kwargs)

    monkeypatch.setattr(models, "create_async_engine", spy)
    return recorded


def use_local(monkeypatch: pytest.MonkeyPatch, environment: Environment) -> None:
    monkeypatch.setattr(settings, "environment", environment)
    monkeypatch.setattr(settings, "postgres_user", "postgres")
    monkeypatch.setattr(settings, "postgres_password", "p@ss:w/rd")
    monkeypatch.setattr(settings, "db_host", "db")
    monkeypatch.setattr(settings, "postgres_db_dev", "f4k")
    monkeypatch.setattr(settings, "postgres_db_test", "f4k_test")
    monkeypatch.setattr(settings, "database_url", "")


def use_production(monkeypatch: pytest.MonkeyPatch, database_url: str) -> None:
    monkeypatch.setattr(settings, "environment", Environment.PRODUCTION)
    monkeypatch.setattr(settings, "database_url", database_url)


NEON_URL = "postgresql://neon_owner:p%40ss%3Aw%2Frd@ep-x.neon.tech/neondb"


def engines() -> tuple[URL, URL]:
    assert models.engine is not None
    assert models.async_engine is not None
    return models.engine.url, models.async_engine.url


class TestLocal:
    @pytest.mark.parametrize(
        ("environment", "database"),
        [(Environment.DEVELOPMENT, "f4k"), (Environment.TESTING, "f4k_test")],
    )
    def test_both_engines_point_at_the_same_local_database(
        self,
        monkeypatch: pytest.MonkeyPatch,
        environment: Environment,
        database: str,
    ) -> None:
        use_local(monkeypatch, environment)
        models.init_database()
        sync_url, async_url = engines()
        assert sync_url.drivername == "postgresql"
        assert async_url.drivername == "postgresql+asyncpg"
        for url in (sync_url, async_url):
            assert url.username == "postgres"
            assert url.password == "p@ss:w/rd"
            assert (url.host, url.port, url.database) == ("db", 5432, database)
            assert dict(url.query) == {}

    def test_local_engines_echo_sql(self, monkeypatch: pytest.MonkeyPatch) -> None:
        use_local(monkeypatch, Environment.DEVELOPMENT)
        models.init_database()
        assert models.engine is not None and models.engine.echo
        assert models.async_engine is not None and models.async_engine.echo

    def test_async_engine_gets_no_ssl_connect_args(
        self, monkeypatch: pytest.MonkeyPatch, async_engine_kwargs: dict[str, Any]
    ) -> None:
        use_local(monkeypatch, Environment.DEVELOPMENT)
        models.init_database()
        assert async_engine_kwargs["connect_args"] == {}


class TestProduction:
    def test_both_engines_come_from_database_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_production(monkeypatch, NEON_URL)
        models.init_database()
        sync_url, async_url = engines()
        assert sync_url.drivername == "postgresql"
        assert async_url.drivername == "postgresql+asyncpg"
        for url in (sync_url, async_url):
            assert url.username == "neon_owner"
            assert url.password == "p@ss:w/rd"
            assert (url.host, url.port, url.database) == (
                "ep-x.neon.tech",
                None,
                "neondb",
            )

    def test_sslmode_moves_from_the_async_url_to_connect_args(
        self, monkeypatch: pytest.MonkeyPatch, async_engine_kwargs: dict[str, Any]
    ) -> None:
        """asyncpg rejects libpq's sslmode/channel_binding as connect kwargs;
        psycopg2 (the sync engine) wants them left in place."""
        use_production(
            monkeypatch, NEON_URL + "?sslmode=require&channel_binding=require"
        )
        models.init_database()
        sync_url, async_url = engines()
        assert dict(sync_url.query) == {
            "sslmode": "require",
            "channel_binding": "require",
        }
        assert dict(async_url.query) == {}
        assert async_engine_kwargs["connect_args"] == {"ssl": "require"}
        assert async_url.password == "p@ss:w/rd"

    def test_other_query_parameters_survive_the_strip(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_production(monkeypatch, NEON_URL + "?sslmode=require&application_name=f4k")
        models.init_database()
        _, async_url = engines()
        assert dict(async_url.query) == {"application_name": "f4k"}

    def test_without_sslmode_the_async_url_is_untouched(
        self, monkeypatch: pytest.MonkeyPatch, async_engine_kwargs: dict[str, Any]
    ) -> None:
        use_production(monkeypatch, NEON_URL + "?application_name=f4k")
        models.init_database()
        _, async_url = engines()
        assert dict(async_url.query) == {"application_name": "f4k"}
        assert async_engine_kwargs["connect_args"] == {}

    def test_production_engines_do_not_echo_sql(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_production(monkeypatch, NEON_URL)
        models.init_database()
        assert models.engine is not None and not models.engine.echo
        assert models.async_engine is not None and not models.async_engine.echo


class TestWiring:
    def test_the_session_maker_is_bound_to_the_async_engine(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_local(monkeypatch, Environment.DEVELOPMENT)
        models.init_database()
        assert models.async_session_maker_instance is not None
        assert models.async_session_maker_instance.kw["bind"] is models.async_engine

    def test_a_missing_credential_leaves_nothing_half_built(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use_local(monkeypatch, Environment.DEVELOPMENT)
        monkeypatch.setattr(settings, "db_host", "")
        with pytest.raises(RuntimeError, match="DB_HOST"):
            models.init_database()
        assert models.engine is None
        assert models.async_engine is None
        assert models.async_session_maker_instance is None

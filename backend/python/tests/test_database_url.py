"""Tests for the single database-URL builder.

The three copies this replaced disagreed with each other, so the cases that
matter are the ones where they differed: which database name each environment
picks, and what happens when a credential is missing.
"""

import pytest
from sqlalchemy import make_url

from app.config import Environment, settings
from app.database_url import ASYNC_DRIVER, SYNC_DRIVER, get_database_url


@pytest.fixture(autouse=True)
def local(monkeypatch: pytest.MonkeyPatch) -> None:
    """A complete set of local credentials, as docker-compose supplies them.

    Autouse: every case here starts from a valid baseline and breaks exactly
    the one thing it is about.
    """
    monkeypatch.setattr(settings, "postgres_user", "postgres")
    monkeypatch.setattr(settings, "postgres_password", "password")
    monkeypatch.setattr(settings, "db_host", "localhost")
    monkeypatch.setattr(settings, "postgres_db_dev", "f4k")
    monkeypatch.setattr(settings, "postgres_db_test", "f4k_test")
    monkeypatch.setattr(settings, "database_url", "")


def use(monkeypatch: pytest.MonkeyPatch, environment: Environment) -> None:
    monkeypatch.setattr(settings, "environment", environment)


class TestDatabaseSelection:
    def test_development_uses_the_dev_database(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use(monkeypatch, Environment.DEVELOPMENT)
        assert make_url(get_database_url()).database == "f4k"

    def test_testing_uses_the_test_database(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use(monkeypatch, Environment.TESTING)
        assert make_url(get_database_url()).database == "f4k_test"

    def test_production_uses_database_url_verbatim(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use(monkeypatch, Environment.PRODUCTION)
        monkeypatch.setattr(
            settings, "database_url", "postgresql://u:p@db.neon.tech:5432/prod"
        )
        url = make_url(get_database_url())
        assert (url.host, url.database) == ("db.neon.tech", "prod")

    def test_production_ignores_the_local_postgres_fields(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The POSTGRES_* fields describe the local container and must not
        leak into a deployed connection just because they carry defaults."""
        use(monkeypatch, Environment.PRODUCTION)
        monkeypatch.setattr(
            settings, "database_url", "postgresql://u:p@db.neon.tech:5432/prod"
        )
        assert "localhost" not in get_database_url()


class TestDrivers:
    @pytest.mark.parametrize(
        "environment", [Environment.DEVELOPMENT, Environment.TESTING]
    )
    def test_async_is_the_default(
        self, monkeypatch: pytest.MonkeyPatch, environment: Environment
    ) -> None:
        use(monkeypatch, environment)
        assert get_database_url().startswith("postgresql+asyncpg://")

    @pytest.mark.parametrize(
        "environment", [Environment.DEVELOPMENT, Environment.TESTING]
    )
    def test_sync_driver_is_requestable(
        self, monkeypatch: pytest.MonkeyPatch, environment: Environment
    ) -> None:
        use(monkeypatch, environment)
        url = get_database_url(SYNC_DRIVER)
        assert url.startswith("postgresql://") and "asyncpg" not in url

    def test_the_driver_swaps_on_a_production_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """DATABASE_URL arrives with whatever driver the provider wrote; both
        engines are built from it, so each has to be able to reclaim it."""
        use(monkeypatch, Environment.PRODUCTION)
        monkeypatch.setattr(
            settings, "database_url", "postgresql://u:p@db.neon.tech:5432/prod"
        )
        assert get_database_url(ASYNC_DRIVER).startswith("postgresql+asyncpg://")
        assert get_database_url(SYNC_DRIVER).startswith("postgresql://")

    def test_query_parameters_survive_the_driver_swap(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Neon's connection string carries sslmode; dropping it silently
        would turn a TLS connection into a plaintext one."""
        use(monkeypatch, Environment.PRODUCTION)
        monkeypatch.setattr(
            settings,
            "database_url",
            "postgresql://u:p@db.neon.tech:5432/prod?sslmode=require",
        )
        assert make_url(get_database_url()).query["sslmode"] == "require"


class TestMissingCredentials:
    @pytest.mark.parametrize(
        ("field", "expected"),
        [
            ("postgres_user", "POSTGRES_USER"),
            ("db_host", "DB_HOST"),
            ("postgres_db_dev", "POSTGRES_DB_DEV"),
        ],
    )
    def test_a_missing_field_names_itself(
        self,
        monkeypatch: pytest.MonkeyPatch,
        field: str,
        expected: str,
    ) -> None:
        use(monkeypatch, Environment.DEVELOPMENT)
        monkeypatch.setattr(settings, field, "")
        with pytest.raises(RuntimeError, match=expected):
            get_database_url()

    def test_testing_names_the_test_database_variable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use(monkeypatch, Environment.TESTING)
        monkeypatch.setattr(settings, "postgres_db_test", "")
        with pytest.raises(RuntimeError, match="POSTGRES_DB_TEST"):
            get_database_url()

    def test_every_missing_field_is_reported_at_once(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """One round trip per missing variable is a miserable way to find out."""
        use(monkeypatch, Environment.DEVELOPMENT)
        for field in ("postgres_user", "db_host", "postgres_db_dev"):
            monkeypatch.setattr(settings, field, "")
        with pytest.raises(RuntimeError) as caught:
            get_database_url()
        for expected in ("POSTGRES_USER", "DB_HOST", "POSTGRES_DB_DEV"):
            assert expected in str(caught.value)

    def test_an_empty_password_is_allowed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Trust auth on a local socket is legitimate; the others are not."""
        use(monkeypatch, Environment.DEVELOPMENT)
        monkeypatch.setattr(settings, "postgres_password", "")
        url = make_url(get_database_url())
        assert url.username == "postgres"
        assert not url.password
        assert url.host == "localhost"

    def test_production_without_database_url_fails_loudly(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        use(monkeypatch, Environment.PRODUCTION)
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            get_database_url()


class TestPasswordEscaping:
    @pytest.mark.parametrize("password", ["p@ss:word", "p/w?x", "p#w", "p%w", "p w"])
    def test_a_password_with_url_syntax_round_trips(
        self, monkeypatch: pytest.MonkeyPatch, password: str
    ) -> None:
        """The f-string interpolation this replaced silently mangled these:
        an "@" in the password ends the userinfo section early."""
        use(monkeypatch, Environment.DEVELOPMENT)
        monkeypatch.setattr(settings, "postgres_password", password)
        url = make_url(get_database_url())
        assert url.password == password
        assert url.host == "localhost"

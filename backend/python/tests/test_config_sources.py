"""Where Settings gets its values, and in what order.

Cloud Run mounts the Secret Manager secret as a JSON file; locally the same
keys arrive as environment variables or .env. A revision-level environment
variable outranks the file, the file outranks .env.
"""

import json
from pathlib import Path

import pytest

from app.config import (
    CLOUD_RUN_SECRETS_FILE,
    REQUIRED_IN_PRODUCTION,
    Environment,
    Settings,
    require_the_secret_mount,
)

# Keys the tests set themselves; cleared from the process environment first so
# conftest's APP_ENV=testing and the container's real .env cannot mask a source.
KEYS = (
    "APP_ENV",
    "DB_HOST",
    "POSTGRES_USER",
    "PREVIEW_DEPLOY",
    *(name.upper() for name in REQUIRED_IN_PRODUCTION),
)

COMPLETE_PRODUCTION = {name.upper(): f"{name}-value" for name in REQUIRED_IN_PRODUCTION}
COMPLETE_PRODUCTION["APP_ENV"] = "production"
COMPLETE_PRODUCTION["DATABASE_URL"] = "postgresql://u:p@db.neon.tech:5432/prod"


@pytest.fixture
def isolated(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    for key in KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setitem(Settings.model_config, "env_file", str(tmp_path / ".env"))
    monkeypatch.setitem(
        Settings.model_config, "json_file", str(tmp_path / "config.json")
    )
    return tmp_path


def write_json(directory: Path, **values: object) -> None:
    (directory / "config.json").write_text(json.dumps(values))


def test_the_mount_path_is_where_cloud_run_puts_the_secret() -> None:
    assert CLOUD_RUN_SECRETS_FILE == "/secrets/config.json"


class TestJsonFile:
    def test_upper_case_keys_populate_the_fields(self, isolated: Path) -> None:
        write_json(isolated, POSTGRES_USER="neondb_owner", DB_HOST="db.example")
        settings = Settings()
        assert settings.postgres_user == "neondb_owner"
        assert settings.db_host == "db.example"

    def test_app_env_reaches_the_aliased_field(self, isolated: Path) -> None:
        write_json(isolated, **COMPLETE_PRODUCTION)
        assert Settings().environment is Environment.PRODUCTION

    def test_a_bad_app_env_still_fails_at_startup(self, isolated: Path) -> None:
        write_json(isolated, APP_ENV="prod")
        with pytest.raises(ValueError, match="APP_ENV"):
            Settings()

    def test_booleans_are_coerced(self, isolated: Path) -> None:
        write_json(isolated, PREVIEW_DEPLOY="true")
        assert Settings().preview_deploy is True

    def test_keys_that_are_not_settings_are_skipped(self, isolated: Path) -> None:
        write_json(isolated, DB_HOST="db.example", ADMIN_AUTH_ID="shared-with-scripts")
        assert Settings().db_host == "db.example"

    @pytest.mark.usefixtures("isolated")
    def test_a_missing_file_means_defaults(self) -> None:
        settings = Settings()
        assert settings.environment is Environment.DEVELOPMENT
        assert settings.db_host == ""


class TestProductionRefusesToStartHalfConfigured:
    def test_a_complete_secret_starts(self, isolated: Path) -> None:
        write_json(isolated, **COMPLETE_PRODUCTION)
        assert Settings().environment is Environment.PRODUCTION

    @pytest.mark.parametrize("name", REQUIRED_IN_PRODUCTION)
    def test_each_required_key_is_named_when_absent(
        self, isolated: Path, name: str
    ) -> None:
        """A typo'd key (POSTGRES_USR) reads as absent, so this is the typo
        case too."""
        values = dict(COMPLETE_PRODUCTION)
        del values[name.upper()]
        write_json(isolated, **values)
        with pytest.raises(ValueError, match=name.upper()):
            Settings()

    def test_an_empty_value_counts_as_missing(self, isolated: Path) -> None:
        write_json(isolated, **{**COMPLETE_PRODUCTION, "GOOGLE_MAPS_API_KEY": ""})
        with pytest.raises(ValueError, match="GOOGLE_MAPS_API_KEY"):
            Settings()

    def test_every_gap_is_reported_at_once(self, isolated: Path) -> None:
        values = dict(COMPLETE_PRODUCTION)
        del values["MAILER_USER"]
        del values["GCP_BUCKET_NAME"]
        write_json(isolated, **values)
        with pytest.raises(ValueError, match="MAILER_USER, GCP_BUCKET_NAME"):
            Settings()

    @pytest.mark.parametrize(
        "environment", [Environment.DEVELOPMENT, Environment.TESTING]
    )
    def test_other_environments_do_not_require_them(
        self, isolated: Path, environment: Environment
    ) -> None:
        write_json(isolated, APP_ENV=environment.value)
        assert Settings().environment is environment


class TestTheCloudRunMount:
    @pytest.fixture
    def on_cloud_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("K_SERVICE", "backend-service")

    @pytest.mark.usefixtures("on_cloud_run")
    def test_a_missing_mount_refuses_to_start(self, tmp_path: Path) -> None:
        with pytest.raises(RuntimeError, match="not mounted"):
            require_the_secret_mount(tmp_path / "config.json")

    @pytest.mark.usefixtures("on_cloud_run")
    def test_a_present_mount_is_fine(self, tmp_path: Path) -> None:
        (tmp_path / "config.json").write_text("{}")
        require_the_secret_mount(tmp_path / "config.json")

    def test_off_cloud_run_nothing_is_required(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.delenv("K_SERVICE", raising=False)
        require_the_secret_mount(tmp_path / "config.json")


class TestPrecedence:
    def test_an_environment_variable_beats_the_file(
        self, isolated: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_json(isolated, DB_HOST="from-json")
        monkeypatch.setenv("DB_HOST", "from-env")
        assert Settings().db_host == "from-env"

    def test_the_file_beats_dotenv(self, isolated: Path) -> None:
        write_json(isolated, DB_HOST="from-json")
        (isolated / ".env").write_text("DB_HOST=from-dotenv\n")
        assert Settings().db_host == "from-json"

    def test_dotenv_fills_what_the_file_leaves_out(self, isolated: Path) -> None:
        write_json(isolated, DB_HOST="from-json")
        (isolated / ".env").write_text("FRONTEND_BASE_URL=https://dotenv.example\n")
        settings = Settings()
        assert settings.db_host == "from-json"
        assert settings.frontend_base_url == "https://dotenv.example"

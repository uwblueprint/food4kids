"""Where Settings gets its values, and in what order.

Cloud Run mounts the Secret Manager secret as a JSON file; locally the same
keys arrive as environment variables or .env. A revision-level environment
variable outranks the file, the file outranks .env.
"""

import json
from pathlib import Path

import pytest

from app.config import CLOUD_RUN_SECRETS_FILE, Environment, Settings

# Keys the tests set themselves; cleared from the process environment first so
# conftest's APP_ENV=testing and CI's POSTGRES_* cannot mask a source.
KEYS = ("APP_ENV", "DB_HOST", "POSTGRES_USER", "PREVIEW_DEPLOY", "FRONTEND_BASE_URL")


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
        write_json(isolated, APP_ENV="production")
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

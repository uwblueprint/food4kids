"""The suite must run as TESTING no matter what APP_ENV the shell exports.

conftest.py forces APP_ENV before importing `app`; if that ordering ever
regresses, `settings` freezes to the shell's value (development inside the
compose container) and the app engine silently targets the dev database.
"""

import os

from app.config import Environment, settings
from app.models import get_database_url


def test_suite_runs_as_testing() -> None:
    assert settings.environment is Environment.TESTING


def test_app_engine_targets_test_database() -> None:
    assert get_database_url().endswith("/" + os.environ["POSTGRES_DB_TEST"])

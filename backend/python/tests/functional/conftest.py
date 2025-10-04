from typing import Any

import pytest
from fastapi.testclient import TestClient

from app import create_app


@pytest.fixture(scope="session", autouse=True)
def client() -> Any:
    app = create_app()
    test_client = TestClient(app)
    yield test_client

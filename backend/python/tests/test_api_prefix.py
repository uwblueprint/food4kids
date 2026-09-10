"""The API is mounted under a prefix, and that is load-bearing.

Firebase Hosting rewrites /api/** to this service and forwards the matched
path verbatim rather than stripping it, so the routes have to carry the prefix
themselves. Serving them at the root instead would not fail loudly — every
request would simply 404 through the rewrite — so it is pinned here.

The auth coverage guard in test_auth_integration.py deliberately strips the
prefix before comparing, which means it would stay green if the prefix
vanished. This is the test that would not.
"""

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app import create_app, routers
from app.routers import API_PREFIX

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


@pytest.fixture(scope="module")
def schema_paths() -> list[str]:
    return [
        path
        for path, operations in create_app().openapi()["paths"].items()
        if any(method in HTTP_METHODS for method in operations)
    ]


def test_the_prefix_is_what_hosting_rewrites() -> None:
    """Hosting's rewrite is configured for this exact string. It is deployed
    config not yet checked in; once frontend/firebase.json lands on main, parse
    it here instead of pinning the literal."""
    assert API_PREFIX == "/api"


def test_every_route_carries_the_prefix(schema_paths: list[str]) -> None:
    unprefixed = sorted(p for p in schema_paths if not p.startswith(f"{API_PREFIX}/"))
    assert not unprefixed, (
        "These routes are exposed outside the prefix and would 404 through the "
        "Hosting rewrite:\n  " + "\n  ".join(unprefixed)
    )


@pytest.fixture(scope="module")
def declared_paths() -> set[str]:
    """Every path the router modules declare, mounted where init_app puts it.
    Read off the routers rather than app.routes, which FastAPI 0.137 no longer
    flattens."""
    paths: set[str] = set()
    for name in dir(routers):
        if not name.endswith("_routes"):
            continue
        for route in getattr(routers, name).router.routes:
            assert isinstance(route, APIRoute), f"{name} nests something: {route!r}"
            if route.include_in_schema:
                paths.add(f"{API_PREFIX}{route.path_format}")
    return paths


def test_the_schema_lists_every_declared_route(
    schema_paths: list[str], declared_paths: set[str]
) -> None:
    """Guards the test above from passing vacuously: what it inspects is exactly
    what the router modules declare, nothing dropped and nothing extra."""
    assert declared_paths
    assert set(schema_paths) == declared_paths


@pytest.fixture(scope="module")
def client() -> TestClient:
    """No context manager: the lifespan wants Firebase and a database, and
    routing is decided before either matters."""
    return TestClient(create_app())


class TestReachability:
    """The prefix has to move the route, not just decorate the schema.

    Asserted as "is there a route here" rather than on a status code: without
    the lifespan a handler that reaches for the database raises, so the status
    reflects the harness, not the auth gate. What that gate returns is
    test_auth_integration.py's job — this is only about where the route lives.
    """

    def test_the_prefixed_path_reaches_a_route(self, client: TestClient) -> None:
        assert client.get(f"{API_PREFIX}/locations/").status_code != 404

    def test_the_unprefixed_path_is_gone(self, client: TestClient) -> None:
        assert client.get("/locations/").status_code == 404


class TestDocsStayAtTheRoot:
    """Hosting only rewrites /api/**, so these are reachable on the Cloud Run
    URL and not through the app domain. That is deliberate — moving them under
    the prefix would publish them on the public site."""

    def test_openapi_json_is_not_prefixed(self, client: TestClient) -> None:
        assert client.get("/openapi.json").status_code == 200
        assert client.get(f"{API_PREFIX}/openapi.json").status_code == 404

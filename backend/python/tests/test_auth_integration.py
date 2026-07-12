"""
Integration tests for route-level authorization wiring.

Unlike test_auth_middleware.py (which tests the auth *dependencies* in isolation
against synthetic routes), this module mounts the **real** application and drives
every auth-bearing endpoint as four different account types, asserting the auth
decision for each. It exists because conftest.py bypasses auth for all other
router tests, so nothing else verifies that the correct guard is wired to the
correct route.

Two tests:

1. ``test_route_auth_matrix`` — for each route with a role/ownership policy,
   request it as an anonymous caller, the owning driver, a different driver, and
   an admin, and assert each is allowed/denied as the policy requires.

2. ``test_every_exposed_route_is_classified`` — a completeness guard: every route
   the app exposes must appear in ROUTE_POLICIES. Adding a new endpoint without
   classifying its auth fails this test, forcing an explicit decision (and, for
   the auth-bearing policies, coverage by the matrix above).

The single source of truth is ROUTE_POLICIES below: a ``(method, path) -> Policy``
registry. ``path`` matches FastAPI's templated path exactly (e.g.
``/drivers/{driver_id}``).
"""

import re
from collections.abc import AsyncGenerator, Iterator
from datetime import datetime
from enum import Enum
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import create_app
from app.dependencies.services import get_gcp_storage_client
from app.models import get_session

# ---------------------------------------------------------------------------
# Policies and actors
# ---------------------------------------------------------------------------


class Policy(str, Enum):
    """The authorization contract for a route."""

    # Role / ownership gates — exercised by the auth matrix test.
    ADMIN_ONLY = "admin_only"
    DRIVER_ONLY = "driver_only"  # drivers only; admins are rejected
    DRIVER_OR_ADMIN = "driver_or_admin"
    SELF_DRIVER_OR_ADMIN = "self_driver_or_admin"
    ROUTE_ASSIGNED_OR_ADMIN = "route_assigned_or_admin"
    ANNOUNCEMENT_OWNER_OR_ADMIN = "announcement_owner_or_admin"
    AUTHENTICATED = "authenticated"  # any signed-in user, no role/ownership check

    # Not behaviourally tested — classified only, for the completeness guard.
    PUBLIC = "public"  # no auth by design (auth infra, registration)


class Actor(str, Enum):
    ANON = "anon"  # no Authorization header
    ADMIN = "admin"  # role=admin
    SELF = "self"  # the driver owning {driver_id} / assigned to {route_id}
    OTHER = "other"  # a different, unrelated driver


# Which actors the auth layer should ALLOW through to the handler. The anonymous
# caller is never allowed for any auth-bearing policy.
ALLOWED_ACTORS: dict[Policy, set[Actor]] = {
    Policy.ADMIN_ONLY: {Actor.ADMIN},
    Policy.DRIVER_ONLY: {Actor.SELF, Actor.OTHER},
    Policy.DRIVER_OR_ADMIN: {Actor.ADMIN, Actor.SELF, Actor.OTHER},
    Policy.SELF_DRIVER_OR_ADMIN: {Actor.ADMIN, Actor.SELF},
    Policy.ROUTE_ASSIGNED_OR_ADMIN: {Actor.ADMIN, Actor.SELF},
    Policy.ANNOUNCEMENT_OWNER_OR_ADMIN: {Actor.ADMIN, Actor.SELF},
    Policy.AUTHENTICATED: {Actor.ADMIN, Actor.SELF, Actor.OTHER},
}

# Policies the matrix test drives. PUBLIC routes are classified only.
AUTH_TESTED: frozenset[Policy] = frozenset(ALLOWED_ACTORS)

# Run the privileged/destructive actor last so any mutation it performs cannot
# affect the auth decision of an actor evaluated earlier in the same request set.
ACTOR_ORDER: tuple[Actor, ...] = (Actor.ANON, Actor.OTHER, Actor.SELF, Actor.ADMIN)

DENY_CODES = {401, 403}


# ---------------------------------------------------------------------------
# The registry: every exposed route -> its auth policy
# ---------------------------------------------------------------------------

ROUTE_POLICIES: dict[tuple[str, str], Policy] = {
    # --- admin ---
    ("GET", "/admins/test"): Policy.ADMIN_ONLY,
    # --- auth infrastructure (public by design) ---
    ("POST", "/auth/login"): Policy.PUBLIC,
    ("POST", "/auth/refresh"): Policy.PUBLIC,
    ("POST", "/auth/logout/{user_id}"): Policy.PUBLIC,
    ("POST", "/auth/resetPassword/{email}"): Policy.PUBLIC,
    # --- drivers ---
    ("GET", "/drivers/"): Policy.DRIVER_OR_ADMIN,
    ("GET", "/drivers/{driver_id}"): Policy.SELF_DRIVER_OR_ADMIN,
    ("PUT", "/drivers/{driver_id}"): Policy.SELF_DRIVER_OR_ADMIN,
    ("DELETE", "/drivers/{driver_id}"): Policy.ADMIN_ONLY,
    ("GET", "/drivers/{driver_id}/history/"): Policy.SELF_DRIVER_OR_ADMIN,
    ("GET", "/drivers/{driver_id}/history/adjustments"): Policy.SELF_DRIVER_OR_ADMIN,
    # Mileage corrections are admin-only — drivers can no longer edit their
    # own km (route-derived km follows assignment; adjustments are appends).
    ("POST", "/drivers/{driver_id}/history/adjustments"): Policy.ADMIN_ONLY,
    ("GET", "/drivers/{driver_id}/history/summary"): Policy.SELF_DRIVER_OR_ADMIN,
    ("GET", "/drivers/{driver_id}/history/{year}/export"): Policy.ADMIN_ONLY,
    # Two-step registration (#117): an admin creates the invite/initial user;
    # /register is auth'd by the invite token in the body, not a bearer token.
    ("POST", "/drivers/initialize"): Policy.ADMIN_ONLY,
    ("POST", "/drivers/register"): Policy.PUBLIC,
    ("POST", "/drivers/test-event-email"): Policy.PUBLIC,
    # --- jobs ---
    ("GET", "/jobs/"): Policy.DRIVER_OR_ADMIN,
    ("POST", "/jobs/generate"): Policy.DRIVER_OR_ADMIN,
    ("GET", "/jobs/{job_id}"): Policy.DRIVER_OR_ADMIN,
    # --- location groups ---
    ("GET", "/location-groups/"): Policy.DRIVER_OR_ADMIN,
    ("POST", "/location-groups/"): Policy.DRIVER_OR_ADMIN,
    ("GET", "/location-groups/{location_group_id}"): Policy.DRIVER_OR_ADMIN,
    ("PATCH", "/location-groups/{location_group_id}"): Policy.DRIVER_OR_ADMIN,
    ("DELETE", "/location-groups/{location_group_id}"): Policy.DRIVER_OR_ADMIN,
    # --- locations ---
    ("GET", "/locations/"): Policy.ADMIN_ONLY,
    ("DELETE", "/locations/"): Policy.ADMIN_ONLY,
    ("POST", "/locations/"): Policy.ADMIN_ONLY,
    ("POST", "/locations/review"): Policy.ADMIN_ONLY,
    ("POST", "/locations/ingest"): Policy.ADMIN_ONLY,
    ("GET", "/locations/{location_id}"): Policy.ADMIN_ONLY,
    ("PATCH", "/locations/{location_id}"): Policy.ADMIN_ONLY,
    ("DELETE", "/locations/{location_id}"): Policy.ADMIN_ONLY,
    # --- system settings ---
    ("GET", "/system-settings/"): Policy.ADMIN_ONLY,
    # --- reports ---
    ("GET", "/reports/deliveries/count"): Policy.ADMIN_ONLY,
    ("GET", "/reports/monthly/{year}/{month}/ranking"): Policy.ADMIN_ONLY,
    ("GET", "/reports/monthly/{year}/{month}/totals"): Policy.ADMIN_ONLY,
    # --- note chains (authenticated, any user) ---
    ("GET", "/note-chains/{note_chain_id}"): Policy.AUTHENTICATED,
    # Deletion is admin-gated inside note_chain_service (not via a dependency).
    ("DELETE", "/note-chains/{note_chain_id}"): Policy.ADMIN_ONLY,
    ("GET", "/note-chains/{note_chain_id}/notes"): Policy.AUTHENTICATED,
    ("POST", "/note-chains/{note_chain_id}/notes"): Policy.AUTHENTICATED,
    ("PATCH", "/note-chains/{note_chain_id}/notes/{note_id}"): Policy.AUTHENTICATED,
    ("DELETE", "/note-chains/{note_chain_id}/notes/{note_id}"): Policy.AUTHENTICATED,
    # --- notes feed ---
    ("GET", "/notes"): Policy.ADMIN_ONLY,
    # --- route groups ---
    ("GET", "/route-groups"): Policy.ADMIN_ONLY,
    ("POST", "/route-groups"): Policy.ADMIN_ONLY,
    ("PATCH", "/route-groups/{route_group_id}"): Policy.ADMIN_ONLY,
    ("DELETE", "/route-groups/{route_group_id}"): Policy.ADMIN_ONLY,
    # --- routes ---
    ("GET", "/routes"): Policy.DRIVER_OR_ADMIN,
    ("GET", "/routes/{route_id}"): Policy.ROUTE_ASSIGNED_OR_ADMIN,
    ("PATCH", "/routes/{route_id}"): Policy.ADMIN_ONLY,
    ("DELETE", "/routes/{route_id}"): Policy.ADMIN_ONLY,
    ("GET", "/routes/{route_id}/google-maps-link"): Policy.ROUTE_ASSIGNED_OR_ADMIN,
    ("GET", "/routes/{route_id}/suggested-driver"): Policy.ADMIN_ONLY,
    # --- announcements ---
    ("GET", "/announcements/"): Policy.DRIVER_OR_ADMIN,
    ("POST", "/announcements/"): Policy.DRIVER_OR_ADMIN,
    ("GET", "/announcements/{announcement_id}"): Policy.DRIVER_OR_ADMIN,
    ("PUT", "/announcements/{announcement_id}"): Policy.ANNOUNCEMENT_OWNER_OR_ADMIN,
    ("DELETE", "/announcements/{announcement_id}"): Policy.ANNOUNCEMENT_OWNER_OR_ADMIN,
    # --- upload (any driver/admin; feeds note + announcement attachments) ---
    ("POST", "/upload/"): Policy.DRIVER_OR_ADMIN,
    # --- system settings ---
    ("PATCH", "/system-settings/"): Policy.ADMIN_ONLY,
    ("POST", "/system-settings/delivery-types/rename"): Policy.ADMIN_ONLY,
    # The route declares a :path converter (/upload/{filename:path}); the
    # OpenAPI schema (our completeness source) renders it without the converter.
    ("DELETE", "/upload/{filename}"): Policy.DRIVER_OR_ADMIN,
}


# ---------------------------------------------------------------------------
# Firebase token mocking — map a bearer token string to decoded claims
# ---------------------------------------------------------------------------

# email_verified is part of the decoded ID token; the ownership deps read it
# from the claim (and require it for everyone, admins included).
_CLAIMS: dict[str, dict[str, Any]] = {
    "tok-admin": {
        "uid": "admin-uid",
        "role": "admin",
        "email": "admin@test.dev",
        "email_verified": True,
    },
    "tok-self": {
        "uid": "self-uid",
        "role": "driver",
        "email": "self@test.dev",
        "email_verified": True,
    },
    "tok-other": {
        "uid": "other-uid",
        "role": "driver",
        "email": "other@test.dev",
        "email_verified": True,
    },
}

_HEADERS: dict[Actor, dict[str, str]] = {
    Actor.ANON: {},
    Actor.ADMIN: {"Authorization": "Bearer tok-admin"},
    Actor.SELF: {"Authorization": "Bearer tok-self"},
    Actor.OTHER: {"Authorization": "Bearer tok-other"},
}


def _fake_verify_id_token(token: str, **_: Any) -> dict:
    # **_ absorbs Firebase's check_revoked kwarg, which callers pass.
    if token in _CLAIMS:
        return dict(_CLAIMS[token])
    raise ValueError("invalid token")


def _fake_get_user(uid: str) -> SimpleNamespace:
    # Defensive: the ownership deps read email_verified from the token claim, but
    # patch get_user too so nothing reaches the real Firebase SDK.
    return SimpleNamespace(uid=uid, email_verified=True, email=f"{uid}@test.dev")


@pytest.fixture
def firebase_auth_mock() -> Iterator[None]:
    """Patch Firebase token verification for the duration of a test."""
    with (
        patch(
            "firebase_admin.auth.verify_id_token",
            side_effect=_fake_verify_id_token,
        ),
        patch("firebase_admin.auth.get_user", side_effect=_fake_get_user),
    ):
        yield


# ---------------------------------------------------------------------------
# Seed data: self driver, other driver, admin user, a route assigned to self
# ---------------------------------------------------------------------------


class Seed(SimpleNamespace):
    self_driver_id: Any
    other_driver_id: Any
    route_group_id: Any
    route_id: Any
    announcement_id: Any


@pytest_asyncio.fixture
async def seed(test_session: AsyncSession) -> Seed:
    """Create the minimal records the auth dependencies look up by auth_id."""
    from app.models.announcement import Announcement
    from app.models.driver import Driver
    from app.models.location import Location
    from app.models.location_group import LocationGroup
    from app.models.route import Route
    from app.models.route_group import RouteGroup
    from app.models.route_stop import RouteStop
    from app.models.user import User

    def _driver(auth_id: str, email: str) -> Driver:
        user = User(
            first_name=auth_id,
            last_name="Driver",
            email=email,
            auth_id=auth_id,
            role="driver",
        )
        test_session.add(user)
        driver = Driver(
            user_id=user.user_id,
            phone="+12125551234",
            address="123 Main St",
            license_plate="ABC123",
            car_make_model="Toyota Camry",
        )
        test_session.add(driver)
        return driver

    self_driver = _driver("self-uid", "self@test.dev")
    other_driver = _driver("other-uid", "other@test.dev")
    location_group = LocationGroup(
        name="Seed Location Group",
        color="#FF5733",
        notes="",
    )

    admin_user = User(
        first_name="Admin",
        last_name="User",
        email="admin@test.dev",
        auth_id="admin-uid",
        role="admin",
    )
    test_session.add(admin_user)
    test_session.add(location_group)

    route_group = RouteGroup(name="Test Group", drive_date=datetime(2025, 3, 1, 8, 0))
    test_session.add(route_group)

    await test_session.commit()
    await test_session.refresh(self_driver)
    await test_session.refresh(other_driver)
    await test_session.refresh(route_group)

    # SELF is assigned to the route (via driver_id); OTHER is not.
    route = Route(
        name="Test Route",
        notes="",
        length=10.0,
        route_group_id=route_group.route_group_id,
        driver_id=self_driver.driver_id,
    )
    location = Location(
        location_group_id=location_group.location_group_id,
        name="Seed Location",
        contact_name="Seed Location",
        address="123 Seed St",
        phone_primary="5550000001",
        num_children=8,
        delivery_type="Family",
    )
    test_session.add_all([route, location])
    await test_session.commit()
    await test_session.refresh(route)
    await test_session.refresh(location)
    announcement = Announcement(
        subject="Seed Announcement",
        message="Seed announcement body",
        user_id=self_driver.user_id,
    )
    test_session.add(announcement)
    await test_session.commit()
    await test_session.refresh(announcement)
    test_session.add(
        RouteStop(
            route_id=route.route_id,
            location_id=location.location_id,
            stop_number=1,
        )
    )
    await test_session.commit()

    return Seed(
        self_driver_id=self_driver.driver_id,
        other_driver_id=other_driver.driver_id,
        route_group_id=route_group.route_group_id,
        route_id=route.route_id,
        announcement_id=announcement.announcement_id,
    )


@pytest_asyncio.fixture
async def auth_client(
    test_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Real app with only the DB session overridden — auth is NOT bypassed."""
    app = create_app()

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield test_session

    app.dependency_overrides[get_session] = override_get_session
    # The GCS client constructs a real google.cloud client eagerly (no creds in
    # tests). Stub it so upload-route dependency resolution succeeds and auth —
    # not a missing-credentials 500 — decides the outcome.
    app.dependency_overrides[get_gcp_storage_client] = MagicMock

    # raise_app_exceptions=False: an unhandled handler exception becomes a 500
    # response (as a real server would return) instead of propagating into the
    # test. This test only cares about the auth decision, and a 500 means auth
    # already let the request reach the handler.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Path templating
# ---------------------------------------------------------------------------


def _fill_path(path: str, seed: Seed) -> str:
    """Substitute path params, pointing ownership params at SELF's resources."""
    values = {
        "driver_id": str(seed.self_driver_id),
        "route_id": str(seed.route_id),
        "announcement_id": str(seed.announcement_id),
        "year": "2025",
    }
    unrelated = str(uuid4())  # for params that ownership doesn't hinge on

    def repl(match: re.Match[str]) -> str:
        name = match.group(1).split(":")[0]  # strip converters like ":path"
        return values.get(name, unrelated)

    return re.sub(r"\{([^}]+)\}", repl, path)


# Routes the matrix exercises, sorted for stable test ids.
_MATRIX_ROUTES = sorted(
    (method, path, policy)
    for (method, path), policy in ROUTE_POLICIES.items()
    if policy in AUTH_TESTED
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.usefixtures("firebase_auth_mock")
@pytest.mark.parametrize(
    ("method", "path", "policy"),
    _MATRIX_ROUTES,
    ids=[f"{m} {p}" for m, p, _ in _MATRIX_ROUTES],
)
async def test_route_auth_matrix(
    method: str,
    path: str,
    policy: Policy,
    auth_client: AsyncClient,
    seed: Seed,
) -> None:
    """Each auth-bearing route allows/denies each account type per its policy.

    Auth is enforced before body validation, so we send no body: a denied actor
    is rejected with 401/403 before the handler runs, and an allowed actor is
    expected NOT to be rejected (any other status — 2xx/404/422/500 — means auth
    let the request through, which is all this test asserts).
    """
    url = _fill_path(path, seed)
    allowed = ALLOWED_ACTORS[policy]
    failures: list[str] = []

    for actor in ACTOR_ORDER:
        resp = await auth_client.request(method, url, headers=_HEADERS[actor])
        denied = resp.status_code in DENY_CODES
        if actor in allowed and denied:
            failures.append(f"{actor.value}: expected ALLOW, got {resp.status_code}")
        elif actor not in allowed and not denied:
            failures.append(
                f"{actor.value}: expected DENY (401/403), got {resp.status_code}"
            )

    assert not failures, (
        f"{method} {path} [{policy.value}] auth mismatches:\n  " + "\n  ".join(failures)
    )


def test_every_exposed_route_is_classified() -> None:
    """Completeness guard: every exposed route must be in ROUTE_POLICIES.

    A new endpoint added without an entry here fails this test, forcing an
    explicit auth decision — and, for the role/ownership policies, coverage by
    test_route_auth_matrix above.
    """
    app = create_app()
    # Enumerate exposed routes from the public OpenAPI schema rather than walking
    # app.routes: FastAPI's internal route structure is version-sensitive (0.137
    # nests included routers behind a lazy wrapper instead of flattening them
    # into app.routes), but the generated schema's path+method map is the stable
    # public contract for what the app exposes. Docs/openapi routes are not in
    # the schema, which is exactly what we want (they carry no auth policy).
    http_methods = {"GET", "POST", "PUT", "PATCH", "DELETE"}
    schema = app.openapi()
    exposed = {
        (method.upper(), path)
        for path, operations in schema["paths"].items()
        for method in operations
        if method.upper() in http_methods
    }
    registered = set(ROUTE_POLICIES)

    unclassified = exposed - registered
    stale = registered - exposed

    assert not unclassified, (
        "These routes are exposed but missing from ROUTE_POLICIES — classify "
        "their auth (and add to the matrix if role/ownership-gated):\n  "
        + "\n  ".join(f"{m} {p}" for m, p in sorted(unclassified))
    )
    assert not stale, (
        "ROUTE_POLICIES has entries for routes that no longer exist — remove "
        "them:\n  " + "\n  ".join(f"{m} {p}" for m, p in sorted(stale))
    )


# ---------------------------------------------------------------------------
# GET /routes driver-scoping (ownership *within* the DRIVER_OR_ADMIN role gate)
# ---------------------------------------------------------------------------
#
# The auth matrix above only checks the role gate (any driver/admin may call
# GET /routes). It does NOT exercise the driver_id query param, which carries a
# finer-grained ownership rule resolved by resolve_route_list_driver_filter:
# admins may scope to any driver (or omit it for all routes); a driver is always
# scoped to their own routes and cannot read another driver's. These tests drive
# the real app (auth NOT bypassed) to lock that rule in.


@pytest_asyncio.fixture
async def scoping_routes(test_session: AsyncSession, seed: Seed) -> dict[str, Any]:
    """Alongside seed's self-assigned route, add an other-driver route and an
    unassigned route in the same group, so a scoped query is distinguishable
    from "all routes"."""
    from app.models.route import Route

    other_route = Route(
        name="Other Route",
        notes="",
        length=4.0,
        route_group_id=seed.route_group_id,
        driver_id=seed.other_driver_id,
    )
    unassigned_route = Route(
        name="Unassigned Route",
        notes="",
        length=5.0,
        route_group_id=seed.route_group_id,
    )
    test_session.add_all([other_route, unassigned_route])
    await test_session.commit()
    await test_session.refresh(other_route)
    await test_session.refresh(unassigned_route)
    return {
        "self_route_id": str(seed.route_id),
        "other_route_id": str(other_route.route_id),
        "unassigned_route_id": str(unassigned_route.route_id),
    }


def _route_ids(resp: Any) -> set[str]:
    return {item["route_id"] for item in resp.json()["items"]}


def _route_by_id(resp: Any, route_id: str) -> dict[str, Any]:
    return next(item for item in resp.json()["items"] if item["route_id"] == route_id)


@pytest.mark.asyncio
@pytest.mark.usefixtures("firebase_auth_mock")
class TestGetRoutesDriverScoping:
    """Ownership rules for the GET /routes driver_id filter."""

    async def test_driver_unscoped_sees_only_own_routes(
        self, auth_client: AsyncClient, scoping_routes: dict[str, Any]
    ) -> None:
        """A driver omitting driver_id is auto-scoped to themselves — they get
        their own route, not the other driver's or the unassigned one."""
        resp = await auth_client.get("/routes", headers=_HEADERS[Actor.SELF])
        assert resp.status_code == 200
        ids = _route_ids(resp)
        assert ids == {scoping_routes["self_route_id"]}
        route = _route_by_id(resp, scoping_routes["self_route_id"])
        assert route["num_stops"] == 1
        assert route["box_total"] == 4

    async def test_driver_scoped_to_self_is_allowed(
        self, auth_client: AsyncClient, seed: Seed, scoping_routes: dict[str, Any]
    ) -> None:
        """A driver may pass their own driver_id explicitly."""
        resp = await auth_client.get(
            "/routes",
            params={"driver_id": str(seed.self_driver_id)},
            headers=_HEADERS[Actor.SELF],
        )
        assert resp.status_code == 200
        assert _route_ids(resp) == {scoping_routes["self_route_id"]}
        route = _route_by_id(resp, scoping_routes["self_route_id"])
        assert route["num_stops"] == 1
        assert route["box_total"] == 4

    async def test_driver_cannot_request_another_drivers_routes(
        self,
        auth_client: AsyncClient,
        seed: Seed,
        scoping_routes: dict[str, Any],  # noqa: ARG002
    ) -> None:
        """A driver passing another driver's id is rejected with 403 (not
        silently re-scoped, and never returning the other driver's routes)."""
        resp = await auth_client.get(
            "/routes",
            params={"driver_id": str(seed.other_driver_id)},
            headers=_HEADERS[Actor.SELF],
        )
        assert resp.status_code == 403

    async def test_admin_can_scope_to_any_driver(
        self, auth_client: AsyncClient, seed: Seed, scoping_routes: dict[str, Any]
    ) -> None:
        """An admin may scope to an arbitrary driver and gets exactly that
        driver's routes."""
        resp = await auth_client.get(
            "/routes",
            params={"driver_id": str(seed.other_driver_id)},
            headers=_HEADERS[Actor.ADMIN],
        )
        assert resp.status_code == 200
        assert _route_ids(resp) == {scoping_routes["other_route_id"]}

    async def test_admin_unscoped_sees_all_routes(
        self, auth_client: AsyncClient, scoping_routes: dict[str, Any]
    ) -> None:
        """An admin omitting driver_id sees every route regardless of
        assignment."""
        resp = await auth_client.get("/routes", headers=_HEADERS[Actor.ADMIN])
        assert resp.status_code == 200
        ids = _route_ids(resp)
        assert ids == {
            scoping_routes["self_route_id"],
            scoping_routes["other_route_id"],
            scoping_routes["unassigned_route_id"],
        }
        route = _route_by_id(resp, scoping_routes["self_route_id"])
        assert route["num_stops"] == 1
        assert route["box_total"] == 4

    async def test_driver_unassigned_only_is_rejected(
        self,
        auth_client: AsyncClient,
        scoping_routes: dict[str, Any],  # noqa: ARG002
    ) -> None:
        """A driver is auto-scoped to themselves, so unassigned_only (which
        means driver_id IS NULL) is contradictory and rejected with 400 — a
        driver can never list unassigned routes."""
        resp = await auth_client.get(
            "/routes",
            params={"unassigned_only": "true"},
            headers=_HEADERS[Actor.SELF],
        )
        assert resp.status_code == 400

    async def test_admin_unassigned_only_with_driver_id_is_rejected(
        self,
        auth_client: AsyncClient,
        seed: Seed,
        scoping_routes: dict[str, Any],  # noqa: ARG002
    ) -> None:
        """unassigned_only + an explicit driver scope is contradictory -> 400."""
        resp = await auth_client.get(
            "/routes",
            params={
                "unassigned_only": "true",
                "driver_id": str(seed.other_driver_id),
            },
            headers=_HEADERS[Actor.ADMIN],
        )
        assert resp.status_code == 400

    async def test_admin_unassigned_only_alone_is_allowed(
        self, auth_client: AsyncClient, scoping_routes: dict[str, Any]
    ) -> None:
        """unassigned_only without a driver scope still works for admins and
        returns only the unassigned route."""
        resp = await auth_client.get(
            "/routes",
            params={"unassigned_only": "true"},
            headers=_HEADERS[Actor.ADMIN],
        )
        assert resp.status_code == 200
        assert _route_ids(resp) == {scoping_routes["unassigned_route_id"]}

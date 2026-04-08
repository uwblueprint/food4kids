"""
Unit tests for authentication middleware dependencies.

Tests the auth dependency functions in app/dependencies/auth.py by mocking
Firebase and the auth service layer.
"""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import (
    get_access_token,
    get_current_database_user_id,
    get_current_user_email,
    require_admin,
    require_authorization_by_role,
    require_route_assigned_or_admin,
    require_self_driver_or_admin,
)
from app.models import get_session

# ---------------------------------------------------------------------------
# Helpers — minimal FastAPI app wired with a single auth dependency
# ---------------------------------------------------------------------------

_mock_session = AsyncMock(spec=AsyncSession)


async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
    yield _mock_session


def _make_app(dependency: Any) -> FastAPI:
    """Create a minimal FastAPI app with one protected route and mocked DB session."""
    app = FastAPI()
    app.dependency_overrides[get_session] = _override_get_session

    @app.get("/protected")
    async def protected(auth: Any = Depends(dependency)) -> dict:
        return {"auth": str(auth)}

    return app


async def _get(app: FastAPI, headers: dict[str, str] | None = None) -> Any:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        return await ac.get("/protected", headers=headers or {})


# ---------------------------------------------------------------------------
# get_access_token
# ---------------------------------------------------------------------------


class TestGetAccessToken:
    @pytest.mark.asyncio
    async def test_valid_bearer_token(self) -> None:
        """Bearer token is extracted from Authorization header."""
        app = _make_app(get_access_token)
        resp = await _get(app, {"Authorization": "Bearer my-token-123"})
        assert resp.status_code == 200
        assert resp.json()["auth"] == "my-token-123"

    @pytest.mark.asyncio
    async def test_missing_auth_header_rejects(self) -> None:
        """No Authorization header is rejected."""
        app = _make_app(get_access_token)
        resp = await _get(app)
        assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# require_authorization_by_role
# ---------------------------------------------------------------------------


class TestRequireAuthorizationByRole:
    @pytest.mark.asyncio
    async def test_authorized_role_passes(self) -> None:
        """User with matching role gets 200."""
        dep = require_authorization_by_role({"admin"})
        app = _make_app(dep)

        with patch(
            "app.dependencies.auth.auth_service.is_authorized_by_role",
            new_callable=AsyncMock,
            return_value=True,
        ):
            resp = await _get(app, {"Authorization": "Bearer tok"})

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_unauthorized_role_returns_403(self) -> None:
        """User without matching role gets 403."""
        dep = require_authorization_by_role({"admin"})
        app = _make_app(dep)

        with patch(
            "app.dependencies.auth.auth_service.is_authorized_by_role",
            new_callable=AsyncMock,
            return_value=False,
        ):
            resp = await _get(app, {"Authorization": "Bearer tok"})

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_multiple_roles_any_match_passes(self) -> None:
        """User matching any role in the set gets 200."""
        dep = require_authorization_by_role({"admin", "driver"})
        app = _make_app(dep)

        with patch(
            "app.dependencies.auth.auth_service.is_authorized_by_role",
            new_callable=AsyncMock,
            return_value=True,
        ):
            resp = await _get(app, {"Authorization": "Bearer tok"})

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# require_admin (pre-built dependency)
# ---------------------------------------------------------------------------


class TestRequireAdmin:
    @pytest.mark.asyncio
    async def test_admin_passes(self) -> None:
        app = _make_app(require_admin)

        with patch(
            "app.dependencies.auth.auth_service.is_authorized_by_role",
            new_callable=AsyncMock,
            return_value=True,
        ):
            resp = await _get(app, {"Authorization": "Bearer tok"})

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_non_admin_returns_403(self) -> None:
        app = _make_app(require_admin)

        with patch(
            "app.dependencies.auth.auth_service.is_authorized_by_role",
            new_callable=AsyncMock,
            return_value=False,
        ):
            resp = await _get(app, {"Authorization": "Bearer tok"})

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# get_current_user_email
# ---------------------------------------------------------------------------


class TestGetCurrentUserEmail:
    @pytest.mark.asyncio
    async def test_returns_email_from_token(self) -> None:
        app = _make_app(get_current_user_email)

        with patch(
            "app.dependencies.auth.firebase_admin.auth.verify_id_token",
            return_value={"uid": "uid-1", "email": "test@example.com"},
        ):
            resp = await _get(app, {"Authorization": "Bearer tok"})

        assert resp.status_code == 200
        assert resp.json()["auth"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self) -> None:
        app = _make_app(get_current_user_email)

        with patch(
            "app.dependencies.auth.firebase_admin.auth.verify_id_token",
            side_effect=Exception("expired"),
        ):
            resp = await _get(app, {"Authorization": "Bearer bad"})

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# get_current_database_user_id
# ---------------------------------------------------------------------------


class TestGetCurrentDatabaseUserId:
    @pytest.mark.asyncio
    async def test_returns_database_uuid(self) -> None:
        db_user_id = uuid4()
        app = _make_app(get_current_database_user_id)

        with (
            patch(
                "app.dependencies.auth.firebase_admin.auth.verify_id_token",
                return_value={"uid": "fb-uid", "email": "a@b.com"},
            ),
            patch(
                "app.dependencies.auth.user_service.get_user_id_by_auth_id",
                new_callable=AsyncMock,
                return_value=db_user_id,
            ),
        ):
            resp = await _get(app, {"Authorization": "Bearer tok"})

        assert resp.status_code == 200
        assert resp.json()["auth"] == str(db_user_id)

    @pytest.mark.asyncio
    async def test_user_not_found_returns_401(self) -> None:
        app = _make_app(get_current_database_user_id)

        with (
            patch(
                "app.dependencies.auth.firebase_admin.auth.verify_id_token",
                return_value={"uid": "fb-uid", "email": "a@b.com"},
            ),
            patch(
                "app.dependencies.auth.user_service.get_user_id_by_auth_id",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            resp = await _get(app, {"Authorization": "Bearer tok"})

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self) -> None:
        app = _make_app(get_current_database_user_id)

        with patch(
            "app.dependencies.auth.firebase_admin.auth.verify_id_token",
            side_effect=Exception("revoked"),
        ):
            resp = await _get(app, {"Authorization": "Bearer bad"})

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Missing token — all protected dependencies should reject
# ---------------------------------------------------------------------------


class TestMissingToken:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "dep",
        [
            get_current_user_email,
            get_current_database_user_id,
            require_admin,
        ],
    )
    async def test_no_auth_header_rejects(self, dep: Any) -> None:
        """All auth dependencies reject requests without Authorization header."""
        app = _make_app(dep)
        resp = await _get(app)
        assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Helpers for path-param-based dependencies
# ---------------------------------------------------------------------------


def _make_driver_id_app() -> FastAPI:
    """App with GET /drivers/{driver_id} protected by require_self_driver_or_admin."""
    app = FastAPI()
    app.dependency_overrides[get_session] = _override_get_session

    @app.get("/drivers/{driver_id}")
    async def get_driver(
        driver_id: str, _auth: Any = Depends(require_self_driver_or_admin)
    ) -> dict:
        return {"driver_id": driver_id}

    return app


async def _get_driver(
    app: FastAPI, driver_id: str, headers: dict[str, str] | None = None
) -> Any:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        return await ac.get(f"/drivers/{driver_id}", headers=headers or {})


def _make_route_id_app() -> FastAPI:
    """App with GET /routes/{route_id} protected by require_route_assigned_or_admin."""
    app = FastAPI()
    app.dependency_overrides[get_session] = _override_get_session

    @app.get("/routes/{route_id}")
    async def get_route(
        route_id: str, _auth: Any = Depends(require_route_assigned_or_admin)
    ) -> dict:
        return {"route_id": route_id}

    return app


async def _get_route(
    app: FastAPI, route_id: str, headers: dict[str, str] | None = None
) -> Any:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        return await ac.get(f"/routes/{route_id}", headers=headers or {})


# ---------------------------------------------------------------------------
# require_self_driver_or_admin
# ---------------------------------------------------------------------------


class TestRequireSelfDriverOrAdmin:
    @pytest.mark.asyncio
    async def test_admin_can_access_any_driver(self) -> None:
        """Admin role bypasses the driver_id ownership check."""
        app = _make_driver_id_app()
        driver_id = str(uuid4())

        with patch(
            "app.dependencies.auth.firebase_admin.auth.verify_id_token",
            return_value={"uid": "admin-uid", "role": "admin"},
        ):
            resp = await _get_driver(app, driver_id, {"Authorization": "Bearer tok"})

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_driver_can_access_own_id(self) -> None:
        """Driver accessing their own driver_id gets 200."""
        app = _make_driver_id_app()
        driver_id = str(uuid4())

        with (
            patch(
                "app.dependencies.auth.firebase_admin.auth.verify_id_token",
                return_value={"uid": "driver-uid", "role": "driver"},
            ),
            patch(
                "app.dependencies.auth.auth_service.is_authorized_by_driver_id",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            resp = await _get_driver(app, driver_id, {"Authorization": "Bearer tok"})

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_driver_cannot_access_other_driver(self) -> None:
        """Driver accessing a different driver_id gets 403."""
        app = _make_driver_id_app()
        driver_id = str(uuid4())

        with (
            patch(
                "app.dependencies.auth.firebase_admin.auth.verify_id_token",
                return_value={"uid": "driver-uid", "role": "driver"},
            ),
            patch(
                "app.dependencies.auth.auth_service.is_authorized_by_driver_id",
                new_callable=AsyncMock,
                return_value=False,
            ),
        ):
            resp = await _get_driver(app, driver_id, {"Authorization": "Bearer tok"})

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self) -> None:
        """Expired/invalid token returns 401."""
        app = _make_driver_id_app()
        driver_id = str(uuid4())

        with patch(
            "app.dependencies.auth.firebase_admin.auth.verify_id_token",
            side_effect=Exception("token expired"),
        ):
            resp = await _get_driver(app, driver_id, {"Authorization": "Bearer bad"})

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_token_rejects(self) -> None:
        """No Authorization header is rejected."""
        app = _make_driver_id_app()
        resp = await _get_driver(app, str(uuid4()))
        assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# require_route_assigned_or_admin
# ---------------------------------------------------------------------------


class TestRequireRouteAssignedOrAdmin:
    @pytest.mark.asyncio
    async def test_admin_can_access_any_route(self) -> None:
        """Admin role bypasses the route assignment check."""
        app = _make_route_id_app()
        route_id = str(uuid4())

        with patch(
            "app.dependencies.auth.firebase_admin.auth.verify_id_token",
            return_value={"uid": "admin-uid", "role": "admin"},
        ):
            resp = await _get_route(app, route_id, {"Authorization": "Bearer tok"})

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_assigned_driver_can_access_route(self) -> None:
        """Driver assigned to the route gets 200."""
        app = _make_route_id_app()
        route_id = str(uuid4())
        driver_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalar = lambda: True

        with (
            patch(
                "app.dependencies.auth.firebase_admin.auth.verify_id_token",
                return_value={"uid": "driver-uid", "role": "driver"},
            ),
            patch(
                "app.dependencies.auth.driver_service.get_driver_id_by_auth_id",
                new_callable=AsyncMock,
                return_value=driver_id,
            ),
            patch.object(
                _mock_session,
                "execute",
                new_callable=AsyncMock,
                return_value=mock_result,
            ),
        ):
            resp = await _get_route(app, route_id, {"Authorization": "Bearer tok"})

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_unassigned_driver_gets_403(self) -> None:
        """Driver not assigned to the route gets 403."""
        app = _make_route_id_app()
        route_id = str(uuid4())
        driver_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalar = lambda: False

        with (
            patch(
                "app.dependencies.auth.firebase_admin.auth.verify_id_token",
                return_value={"uid": "driver-uid", "role": "driver"},
            ),
            patch(
                "app.dependencies.auth.driver_service.get_driver_id_by_auth_id",
                new_callable=AsyncMock,
                return_value=driver_id,
            ),
            patch.object(
                _mock_session,
                "execute",
                new_callable=AsyncMock,
                return_value=mock_result,
            ),
        ):
            resp = await _get_route(app, route_id, {"Authorization": "Bearer tok"})

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_driver_not_in_db_gets_403(self) -> None:
        """Driver whose auth_id has no matching driver record gets 403."""
        app = _make_route_id_app()
        route_id = str(uuid4())

        with (
            patch(
                "app.dependencies.auth.firebase_admin.auth.verify_id_token",
                return_value={"uid": "driver-uid", "role": "driver"},
            ),
            patch(
                "app.dependencies.auth.driver_service.get_driver_id_by_auth_id",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            resp = await _get_route(app, route_id, {"Authorization": "Bearer tok"})

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self) -> None:
        """Expired/invalid token returns 401."""
        app = _make_route_id_app()
        route_id = str(uuid4())

        with patch(
            "app.dependencies.auth.firebase_admin.auth.verify_id_token",
            side_effect=Exception("token expired"),
        ):
            resp = await _get_route(app, route_id, {"Authorization": "Bearer bad"})

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_token_rejects(self) -> None:
        """No Authorization header is rejected."""
        app = _make_route_id_app()
        resp = await _get_route(app, str(uuid4()))
        assert resp.status_code in (401, 403)

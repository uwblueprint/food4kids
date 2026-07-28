"""A `users` row that is neither a driver nor an admin cannot authenticate.

Defence in depth for orphaned identities: whatever leaves a stranded `users`
row — a bug in a delete path, a half-finished migration, a manual DB edit —
should not leave a working login behind it. `UserService.get_user_by_email` is
the single lookup both `/auth/login` and `/auth/forgot-password` go through, so
the check lives there and both endpoints inherit it.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.driver import Driver
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User

pytestmark = pytest.mark.asyncio

PASSWORD = "correct horse battery staple"


async def _make_user(
    session: AsyncSession, *, email: str, role: str, with_driver: bool
) -> User:
    user = User(
        first_name="Test",
        last_name="Person",
        email=email,
        role=role,
        auth_id=f"auth-{uuid4()}",
    )
    session.add(user)
    await session.flush()

    if with_driver:
        session.add(
            Driver(
                user_id=user.user_id,
                phone="+12125551234",
                address="123 Main St, City, State 12345",
                license_plate="ABC123",
                car_make_model="Toyota Camry",
            )
        )

    await session.commit()
    return user


def _firebase_accepts_the_password() -> Any:
    """Sign-in succeeds, so the DB check is the only thing under test."""
    token = MagicMock()
    token.access_token = "access-token"
    token.refresh_token = "refresh-token"
    return patch(
        "app.utilities.firebase_rest_client.FirebaseRestClient.sign_in_with_password",
        return_value=token,
    )


# ---------------------------------------------------------------------------
# /auth/login
# ---------------------------------------------------------------------------


async def test_driver_with_a_driver_row_can_log_in(
    async_client: AsyncClient, test_session: AsyncSession
) -> None:
    """The guard must not lock out the ordinary case."""
    await _make_user(
        test_session, email="real.driver@example.com", role="driver", with_driver=True
    )

    with _firebase_accepts_the_password():
        response = await async_client.post(
            "/auth/login",
            json={"email": "real.driver@example.com", "password": PASSWORD},
        )

    assert response.status_code == 200
    assert response.json()["email"] == "real.driver@example.com"


async def test_admin_without_a_driver_row_can_log_in(
    async_client: AsyncClient, test_session: AsyncSession
) -> None:
    """Admins never have a `drivers` row — the role is what admits them."""
    await _make_user(
        test_session, email="boss@example.com", role="admin", with_driver=False
    )

    with _firebase_accepts_the_password():
        response = await async_client.post(
            "/auth/login", json={"email": "boss@example.com", "password": PASSWORD}
        )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


async def test_orphaned_user_cannot_log_in(
    async_client: AsyncClient, test_session: AsyncSession
) -> None:
    """No driver row and not an admin: refused, even though Firebase said yes."""
    await _make_user(
        test_session, email="orphan@example.com", role="driver", with_driver=False
    )

    with _firebase_accepts_the_password():
        response = await async_client.post(
            "/auth/login", json={"email": "orphan@example.com", "password": PASSWORD}
        )

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# /auth/forgot-password
# ---------------------------------------------------------------------------


async def test_orphaned_user_gets_no_password_reset_token(
    async_client: AsyncClient, test_session: AsyncSession
) -> None:
    """204 either way (anti-enumeration), so assert on the token and the email."""
    await _make_user(
        test_session, email="orphan@example.com", role="driver", with_driver=False
    )

    with patch(
        "app.services.implementations.email_dispatcher.EmailDispatcher.dispatch",
        new_callable=AsyncMock,
    ) as dispatch:
        response = await async_client.post(
            "/auth/forgot-password", json={"email": "orphan@example.com"}
        )

    assert response.status_code == 204
    dispatch.assert_not_called()
    tokens = (await test_session.execute(select(PasswordResetToken))).scalars().all()
    assert tokens == []


async def test_real_driver_still_gets_a_password_reset_token(
    async_client: AsyncClient, test_session: AsyncSession
) -> None:
    """The other half of the contract: a real driver's reset still works."""
    await _make_user(
        test_session, email="real.driver@example.com", role="driver", with_driver=True
    )

    with patch(
        "app.services.implementations.email_dispatcher.EmailDispatcher.dispatch",
        new_callable=AsyncMock,
    ) as dispatch:
        response = await async_client.post(
            "/auth/forgot-password", json={"email": "real.driver@example.com"}
        )

    assert response.status_code == 204
    dispatch.assert_called_once()
    tokens = (await test_session.execute(select(PasswordResetToken))).scalars().all()
    assert len(tokens) == 1

"""Admin account bootstrapping: the CLI, and the registration it hands off to.

Two halves have to line up for an admin account to work at all, and only one of
them lives in Postgres:

* ``python -m app.create_admin`` writes the ``users``/``admin_info``/
  ``user_invites`` rows and prints a create-password link;
* ``POST /auth/register`` turns that link into a Firebase user carrying the
  ``role: admin`` custom claim, and writes ``auth_id`` back onto the row.

Authorization reads the *claim* (``app/dependencies/auth.py``), never
``users.role``, so a test that only checks the database would pass on an
account that can do nothing. The register tests below assert both halves.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.create_admin import (
    EmailAlreadyRegisteredError,
    create_admin_account,
    split_name,
)
from app.models.admin import Admin
from app.models.driver import Driver
from app.models.user import User
from app.models.user_invite import UserInvite
from app.schemas.auth import AuthResponse
from app.utilities.utils import build_invite_url

ADMIN_ARGS = {
    "email": "jane.admin@example.com",
    "first_name": "Jane",
    "last_name": "Admin",
    "phone": "519-576-3443",
}


async def _count(session: AsyncSession, model: Any) -> int:
    return int(await session.scalar(select(func.count()).select_from(model)) or 0)


class TestCreateAdminCli:
    """``app.create_admin`` — the non-destructive bootstrap tool."""

    @pytest.mark.asyncio
    async def test_creates_a_usable_invite(self, test_session: AsyncSession) -> None:
        """One admin user, one admin_info row, one live invite — and a link."""
        invite = await create_admin_account(test_session, **ADMIN_ARGS)

        user = await test_session.scalar(
            select(User).where(User.email == ADMIN_ARGS["email"])
        )
        assert user is not None
        assert user.role == "admin"
        # Still hanging: the Firebase account only exists once the link is used.
        assert user.auth_id is None

        admin = await test_session.scalar(
            select(Admin).where(Admin.user_id == user.user_id)
        )
        assert admin is not None
        # Normalized on the way in, same as every other phone in the schema.
        assert admin.admin_phone == "tel:+1-519-576-3443"

        assert invite.user_id == user.user_id
        assert invite.is_used is False
        assert invite.expires_at > datetime.now(timezone.utc)
        # The 48h default is the product decision; pin it so a silent change to
        # UserInviteBase can't quietly shorten or extend what the CLI promises.
        assert invite.expires_at < datetime.now(timezone.utc) + timedelta(days=2)
        assert invite.expires_at > datetime.now(timezone.utc) + timedelta(
            days=2, minutes=-5
        )

        assert build_invite_url(invite.user_invite_id).endswith(
            f"/create-password/{invite.user_invite_id}"
        )

    @pytest.mark.asyncio
    async def test_touches_no_other_table(self, test_session: AsyncSession) -> None:
        """Unlike seed_database, this deletes nothing and creates nothing else."""
        await create_admin_account(test_session, **ADMIN_ARGS)

        assert await _count(test_session, User) == 1
        assert await _count(test_session, Admin) == 1
        assert await _count(test_session, UserInvite) == 1
        assert await _count(test_session, Driver) == 0

    @pytest.mark.asyncio
    async def test_duplicate_email_is_refused(self, test_session: AsyncSession) -> None:
        """``users.email`` is unique; the second run must not half-commit."""
        await create_admin_account(test_session, **ADMIN_ARGS)

        with pytest.raises(EmailAlreadyRegisteredError, match=ADMIN_ARGS["email"]):
            await create_admin_account(
                test_session,
                **{**ADMIN_ARGS, "first_name": "Someone", "phone": "5195763443"},
            )

        # No orphaned admin_info or invite from the refused attempt.
        assert await _count(test_session, User) == 1
        assert await _count(test_session, Admin) == 1
        assert await _count(test_session, UserInvite) == 1

    @pytest.mark.asyncio
    async def test_duplicate_email_refused_for_an_existing_driver(
        self, test_session: AsyncSession, test_driver: Any
    ) -> None:
        """The clash is on ``users``, so an existing driver blocks it too."""
        existing_email = await test_session.scalar(
            select(User.email).where(User.user_id == test_driver.user_id)
        )
        assert existing_email is not None

        with pytest.raises(EmailAlreadyRegisteredError):
            await create_admin_account(
                test_session, **{**ADMIN_ARGS, "email": existing_email}
            )

        assert await _count(test_session, Admin) == 0
        assert await _count(test_session, UserInvite) == 0

    @pytest.mark.asyncio
    async def test_invalid_phone_is_rejected_before_any_write(
        self, test_session: AsyncSession
    ) -> None:
        """admin_info.admin_phone is NOT NULL and validated — fail, don't guess."""
        with pytest.raises(ValidationError):
            await create_admin_account(
                test_session, **{**ADMIN_ARGS, "phone": "555-1234"}
            )

    @pytest.mark.asyncio
    async def test_invalid_email_is_rejected(self, test_session: AsyncSession) -> None:
        with pytest.raises(ValidationError):
            await create_admin_account(
                test_session, **{**ADMIN_ARGS, "email": "not-an-email"}
            )
        assert await _count(test_session, User) == 0

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("Jane Doe", ("Jane", "Doe")),
            ("  Jane   Doe  ", ("Jane", "Doe")),
            ("Maria del Carmen Rodriguez", ("Maria", "del Carmen Rodriguez")),
            ("Jane\tDoe", ("Jane", "Doe")),
        ],
    )
    def test_split_name(self, name: str, expected: tuple[str, str]) -> None:
        assert split_name(name) == expected

    @pytest.mark.parametrize("name", ["Jane", "", "   "])
    def test_split_name_needs_two_parts(self, name: str) -> None:
        """``users.first_name``/``last_name`` are both NOT NULL, min_length 1."""
        with pytest.raises(ValueError, match="first and last name"):
            split_name(name)


def _fake_auth_response(role: str, email: str) -> AuthResponse:
    return AuthResponse(
        access_token="fake-access-token",
        id=uuid4(),
        first_name="Jane",
        last_name="Admin",
        email=email,
        role=role,
        remember_me=False,
    )


class TestRegister:
    """``POST /auth/register`` — role-agnostic, driven by the invite's user."""

    @staticmethod
    async def _invite_for(
        session: AsyncSession, *, role: str, email: str
    ) -> UserInvite:
        user = User(
            first_name="Jane",
            last_name="Admin" if role == "admin" else "Driver",
            email=email,
            auth_id=None,
            role=role,
        )
        session.add(user)
        await session.flush()

        if role == "admin":
            session.add(Admin(user_id=user.user_id, admin_phone="519-576-3443"))
        else:
            session.add(
                Driver(
                    user_id=user.user_id,
                    phone="+12125551234",
                    address="123 Main St, City, State 12345",
                    license_plate="ABC123",
                    car_make_model="Toyota Camry",
                )
            )

        invite = UserInvite(user_id=user.user_id)
        session.add(invite)
        await session.flush()
        return invite

    async def _register(
        self,
        async_client: AsyncClient,
        invite_id: UUID,
        *,
        role: str,
        email: str,
        uid: str,
    ) -> tuple[Any, MagicMock]:
        firebase_user = MagicMock()
        firebase_user.uid = uid

        with (
            patch(
                "firebase_admin.auth.create_user", return_value=firebase_user
            ) as create_user,
            patch("firebase_admin.auth.set_custom_user_claims") as set_claims,
            patch("firebase_admin.auth.delete_user"),
            patch(
                "app.services.implementations.auth_service.AuthService.generate_token",
                new_callable=AsyncMock,
                return_value=(_fake_auth_response(role, email), "fake-refresh-token"),
            ),
        ):
            response = await async_client.post(
                "/auth/register",
                json={"user_invite_id": str(invite_id), "password": "Testing123!"},
            )
        assert create_user.called
        return response, set_claims

    @pytest.mark.asyncio
    async def test_admin_invite_sets_claim_and_auth_id(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """Both halves: the Firebase ``role`` claim *and* ``users.auth_id``.

        Either one alone is a broken account — the claim is what authorization
        reads, ``auth_id`` is what links the token back to our row.
        """
        email = "jane.admin@example.com"
        invite = await self._invite_for(test_session, role="admin", email=email)

        response, set_claims = await self._register(
            async_client,
            invite.user_invite_id,
            role="admin",
            email=email,
            uid="admin-uid",
        )

        assert response.status_code == 201
        assert response.json()["role"] == "admin"

        set_claims.assert_called_once()
        uid, claims = set_claims.call_args.args
        assert uid == "admin-uid"
        assert claims["role"] == "admin"

        user = await test_session.scalar(select(User).where(User.email == email))
        assert user is not None
        assert user.auth_id == "admin-uid"

        used = await test_session.scalar(
            select(UserInvite).where(UserInvite.user_invite_id == invite.user_invite_id)
        )
        assert used is not None and used.is_used is True

    @pytest.mark.asyncio
    async def test_driver_invite_still_registers_as_a_driver(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """The admin path must not have quietly promoted the driver path."""
        email = "new.driver@example.com"
        invite = await self._invite_for(test_session, role="driver", email=email)

        response, set_claims = await self._register(
            async_client,
            invite.user_invite_id,
            role="driver",
            email=email,
            uid="driver-uid",
        )

        assert response.status_code == 201
        assert response.json()["role"] == "driver"
        assert set_claims.call_args.args[1]["role"] == "driver"

        user = await test_session.scalar(select(User).where(User.email == email))
        assert user is not None
        assert user.auth_id == "driver-uid"

    @pytest.mark.asyncio
    async def test_unknown_invite_is_403(self, async_client: AsyncClient) -> None:
        response = await async_client.post(
            "/auth/register",
            json={"user_invite_id": str(uuid4()), "password": "Testing123!"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_used_invite_is_403(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        invite = await self._invite_for(
            test_session, role="admin", email="used@example.com"
        )
        invite.is_used = True
        await test_session.flush()

        response = await async_client.post(
            "/auth/register",
            json={"user_invite_id": str(invite.user_invite_id), "password": "Test123!"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_expired_invite_is_403(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        invite = await self._invite_for(
            test_session, role="admin", email="expired@example.com"
        )
        invite.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        await test_session.flush()

        response = await async_client.post(
            "/auth/register",
            json={"user_invite_id": str(invite.user_invite_id), "password": "Test123!"},
        )
        assert response.status_code == 403

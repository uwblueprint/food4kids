"""DELETE /drivers/{driver_id} is a hard delete of the person.

The bug these cover: the endpoint used to delete only the `drivers` row, so the
`users` row, the `user_invites` row and the Firebase account all survived — a
"deleted" driver could still sign in and still resolve by email for a password
reset. See the `delete_driver` docstring for what the endpoint removes, what it
deliberately keeps, and why the Firebase delete happens before the DB commit.
"""

from datetime import time
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.driver import Driver
from app.models.note import Note
from app.models.note_chain import NoteChain
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.models.user_invite import UserInvite

pytestmark = pytest.mark.asyncio


DRIVER_PAYLOAD = {
    "first_name": "Dana",
    "last_name": "Delete",
    "email": "dana.delete@example.com",
    "phone": "+12125551234",
    "address": "123 Main St, City, State 12345",
    "license_plate": "DEL123",
    "car_make_model": "Toyota Camry",
}


async def _initialize_driver(
    async_client: AsyncClient, **overrides: Any
) -> dict[str, Any]:
    """Create a driver the way an admin does: POST /drivers/initialize.

    Leaves the driver in the pre-signup state the endpoint produces —
    `auth_id IS NULL`, with an unused `user_invites` row.
    """
    with patch(
        "app.services.implementations.email_dispatcher.EmailDispatcher.dispatch",
        new_callable=AsyncMock,
    ):
        response = await async_client.post(
            "/drivers/initialize", json={**DRIVER_PAYLOAD, **overrides}
        )
    assert response.status_code == 201, response.text
    result: dict[str, Any] = response.json()
    return result


async def _complete_signup(
    session: AsyncSession, user_id: UUID, auth_id: str = "firebase-uid-dana"
) -> None:
    """Stand in for POST /drivers/register: attach a Firebase uid, burn the
    invite. Done directly so these tests exercise delete, not registration."""
    user = (
        await session.execute(select(User).where(User.user_id == user_id))
    ).scalar_one()
    user.auth_id = auth_id

    invite = (
        await session.execute(select(UserInvite).where(UserInvite.user_id == user_id))
    ).scalar_one()
    invite.is_used = True

    await session.commit()


async def _row_counts(session: AsyncSession, user_id: UUID) -> dict[str, int]:
    """Every row that hangs off the user, by table."""
    users = (
        (await session.execute(select(User).where(User.user_id == user_id)))
        .scalars()
        .all()
    )
    drivers = (
        (await session.execute(select(Driver).where(Driver.user_id == user_id)))
        .scalars()
        .all()
    )
    invites = (
        (await session.execute(select(UserInvite).where(UserInvite.user_id == user_id)))
        .scalars()
        .all()
    )
    reset_tokens = (
        (
            await session.execute(
                select(PasswordResetToken).where(PasswordResetToken.user_id == user_id)
            )
        )
        .scalars()
        .all()
    )
    return {
        "users": len(users),
        "drivers": len(drivers),
        "user_invites": len(invites),
        "password_reset_tokens": len(reset_tokens),
    }


# ---------------------------------------------------------------------------
# The reported bug
# ---------------------------------------------------------------------------


async def test_delete_removes_user_invite_and_firebase_account(
    async_client: AsyncClient, test_session: AsyncSession
) -> None:
    """A registered driver's user row, invite row and Firebase account all go."""
    driver = await _initialize_driver(async_client)
    driver_id = UUID(driver["driver_id"])
    user_id = UUID(driver["user_id"])
    await _complete_signup(test_session, user_id)

    assert await _row_counts(test_session, user_id) == {
        "users": 1,
        "drivers": 1,
        "user_invites": 1,
        "password_reset_tokens": 0,
    }

    with patch("firebase_admin.auth.delete_user") as delete_firebase_user:
        response = await async_client.delete(f"/drivers/{driver_id}")

    assert response.status_code == 204
    assert await _row_counts(test_session, user_id) == {
        "users": 0,
        "drivers": 0,
        "user_invites": 0,
        "password_reset_tokens": 0,
    }
    delete_firebase_user.assert_called_once_with("firebase-uid-dana")


async def test_deleted_driver_cannot_log_in(
    async_client: AsyncClient, test_session: AsyncSession
) -> None:
    """Login is refused even if the Firebase credential itself still works.

    The sign-in call is mocked to succeed, so this asserts the *database* half:
    with no `users` row, /auth/login has nobody to issue a session for. Before
    the fix the row survived and this returned 200 with a valid access token.
    """
    driver = await _initialize_driver(async_client)
    user_id = UUID(driver["user_id"])
    await _complete_signup(test_session, user_id)

    with patch("firebase_admin.auth.delete_user"):
        assert (
            await async_client.delete(f"/drivers/{driver['driver_id']}")
        ).status_code == 204

    fake_token = type("Token", (), {"access_token": "a", "refresh_token": "r"})()
    with (
        patch(
            "app.utilities.firebase_rest_client.FirebaseRestClient.sign_in_with_password",
            return_value=fake_token,
        ),
        patch("firebase_admin.auth.get_user_by_email") as get_by_email,
    ):
        get_by_email.return_value.uid = "firebase-uid-dana"
        response = await async_client.post(
            "/auth/login",
            json={"email": DRIVER_PAYLOAD["email"], "password": "hunter2000"},
        )

    assert response.status_code == 401


async def test_deleted_driver_cannot_obtain_a_password_reset_token(
    async_client: AsyncClient, test_session: AsyncSession
) -> None:
    """/auth/forgot-password mints nothing for a deleted driver.

    That endpoint resolves the account by email in `users`, which is exactly
    how a "deleted" driver could still get a fresh reset token. It answers 204
    either way — deliberately, so the response can't be used to enumerate
    addresses — so the assertion that matters is that no token row exists and
    no email was sent.
    """
    driver = await _initialize_driver(async_client)
    await _complete_signup(test_session, UUID(driver["user_id"]))

    with patch("firebase_admin.auth.delete_user"):
        assert (
            await async_client.delete(f"/drivers/{driver['driver_id']}")
        ).status_code == 204

    with (
        patch(
            "app.services.implementations.email_dispatcher.EmailDispatcher.dispatch",
            new_callable=AsyncMock,
        ) as dispatch,
        patch("firebase_admin.auth.get_user_by_email") as get_by_email,
    ):
        # Pretend the Firebase account outlived the delete: the DB lookup is
        # then the only thing standing between a deleted driver and a token.
        get_by_email.return_value.uid = "firebase-uid-dana"
        response = await async_client.post(
            "/auth/forgot-password", json={"email": DRIVER_PAYLOAD["email"]}
        )

    assert response.status_code == 204
    dispatch.assert_not_called()

    tokens = (await test_session.execute(select(PasswordResetToken))).scalars().all()
    assert tokens == []

    by_email = (
        (
            await test_session.execute(
                select(User).where(User.email == DRIVER_PAYLOAD["email"])
            )
        )
        .scalars()
        .all()
    )
    assert by_email == []


async def test_reset_tokens_are_deleted_with_the_driver(
    async_client: AsyncClient, test_session: AsyncSession
) -> None:
    """A reset token issued before the delete must not outlive the account —
    otherwise the link in the driver's inbox still works."""
    driver = await _initialize_driver(async_client)
    user_id = UUID(driver["user_id"])
    await _complete_signup(test_session, user_id)

    test_session.add(PasswordResetToken(user_id=user_id, token_hash="a" * 64))
    await test_session.commit()
    assert (await _row_counts(test_session, user_id))["password_reset_tokens"] == 1

    with patch("firebase_admin.auth.delete_user"):
        assert (
            await async_client.delete(f"/drivers/{driver['driver_id']}")
        ).status_code == 204

    assert (await _row_counts(test_session, user_id))["password_reset_tokens"] == 0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


async def test_delete_driver_who_never_completed_signup(
    async_client: AsyncClient, test_session: AsyncSession
) -> None:
    """`auth_id IS NULL` — there is no Firebase account to delete, and the
    unused invite must not survive as a live signup link."""
    driver = await _initialize_driver(async_client)
    user_id = UUID(driver["user_id"])
    assert driver["auth_id"] is None

    with patch("firebase_admin.auth.delete_user") as delete_firebase_user:
        response = await async_client.delete(f"/drivers/{driver['driver_id']}")

    assert response.status_code == 204
    delete_firebase_user.assert_not_called()
    assert await _row_counts(test_session, user_id) == {
        "users": 0,
        "drivers": 0,
        "user_invites": 0,
        "password_reset_tokens": 0,
    }


async def test_delete_non_existent_driver_is_404(async_client: AsyncClient) -> None:
    response = await async_client.delete(f"/drivers/{uuid4()}")
    assert response.status_code == 404


async def test_delete_is_404_the_second_time(
    async_client: AsyncClient, test_session: AsyncSession
) -> None:
    """Deleting twice is not a partial success — the second call finds nothing."""
    driver = await _initialize_driver(async_client)
    await _complete_signup(test_session, UUID(driver["user_id"]))

    with patch("firebase_admin.auth.delete_user"):
        first = await async_client.delete(f"/drivers/{driver['driver_id']}")
        second = await async_client.delete(f"/drivers/{driver['driver_id']}")

    assert first.status_code == 204
    assert second.status_code == 404


# ---------------------------------------------------------------------------
# Ordering: Firebase before the DB commit
# ---------------------------------------------------------------------------


async def test_firebase_failure_rolls_back_the_whole_delete(
    async_client: AsyncClient, test_session: AsyncSession
) -> None:
    """If Firebase rejects the delete, nothing is removed.

    The endpoint deletes the credential before committing precisely so this
    case leaves a consistent, retryable state rather than a DB-side ghost.
    """
    driver = await _initialize_driver(async_client)
    user_id = UUID(driver["user_id"])
    await _complete_signup(test_session, user_id)

    with patch(
        "firebase_admin.auth.delete_user",
        side_effect=RuntimeError("firebase is down"),
    ):
        response = await async_client.delete(f"/drivers/{driver['driver_id']}")

    assert response.status_code == 500
    assert await _row_counts(test_session, user_id) == {
        "users": 1,
        "drivers": 1,
        "user_invites": 1,
        "password_reset_tokens": 0,
    }


async def test_delete_retries_cleanly_after_a_firebase_failure(
    async_client: AsyncClient, test_session: AsyncSession
) -> None:
    """The admin's second attempt succeeds once Firebase is reachable again."""
    driver = await _initialize_driver(async_client)
    user_id = UUID(driver["user_id"])
    await _complete_signup(test_session, user_id)

    with patch(
        "firebase_admin.auth.delete_user",
        side_effect=RuntimeError("firebase is down"),
    ):
        failed = await async_client.delete(f"/drivers/{driver['driver_id']}")
    assert failed.status_code == 500

    with patch("firebase_admin.auth.delete_user") as delete_firebase_user:
        retry = await async_client.delete(f"/drivers/{driver['driver_id']}")

    assert retry.status_code == 204
    delete_firebase_user.assert_called_once_with("firebase-uid-dana")
    assert await _row_counts(test_session, user_id) == {
        "users": 0,
        "drivers": 0,
        "user_invites": 0,
        "password_reset_tokens": 0,
    }


# ---------------------------------------------------------------------------
# Note chains: the driver's own chain goes, notes they wrote elsewhere stay
# ---------------------------------------------------------------------------


async def test_delete_removes_the_drivers_admin_only_note_chain(
    async_client: AsyncClient, test_session: AsyncSession
) -> None:
    """`create_driver` gives every driver an admin-only chain. Once the driver
    row is gone nothing references it, so it must not be left behind holding
    notes about a deleted person."""
    driver_json = await _initialize_driver(async_client)
    driver_id = UUID(driver_json["driver_id"])
    chain_id = UUID(driver_json["note_chain_id"])

    test_session.add(
        Note(note_chain_id=chain_id, user_id=None, message="Late twice in March.")
    )
    await test_session.commit()

    with patch("firebase_admin.auth.delete_user"):
        assert (await async_client.delete(f"/drivers/{driver_id}")).status_code == 204

    chains = (
        (
            await test_session.execute(
                select(NoteChain).where(NoteChain.note_chain_id == chain_id)
            )
        )
        .scalars()
        .all()
    )
    notes = (
        (await test_session.execute(select(Note).where(Note.note_chain_id == chain_id)))
        .scalars()
        .all()
    )
    assert chains == []
    assert notes == []


async def test_notes_the_driver_wrote_elsewhere_survive_without_an_author(
    async_client: AsyncClient, test_session: AsyncSession
) -> None:
    """A note on a shared chain is an operational record, so it outlives its
    author: the row stays and `user_id` goes NULL (ON DELETE SET NULL).

    Without that FK action the users row could not be deleted at all — the
    delete would fail with a foreign key violation for any driver who had
    actually written a note.
    """
    driver_json = await _initialize_driver(async_client)
    user_id = UUID(driver_json["user_id"])
    await _complete_signup(test_session, user_id)

    shared_chain = NoteChain(read_permission="All", write_permission="All")
    test_session.add(shared_chain)
    await test_session.flush()
    note = Note(
        note_chain_id=shared_chain.note_chain_id,
        user_id=user_id,
        message="Gate code is 4821.",
    )
    test_session.add(note)
    await test_session.commit()
    note_id = note.note_id

    with patch("firebase_admin.auth.delete_user"):
        assert (
            await async_client.delete(f"/drivers/{driver_json['driver_id']}")
        ).status_code == 204

    surviving = (
        await test_session.execute(select(Note).where(Note.note_id == note_id))
    ).scalar_one()
    await test_session.refresh(surviving)
    assert surviving.message == "Gate code is 4821."
    assert surviving.user_id is None


# ---------------------------------------------------------------------------
# Routes are detached, not deleted
# ---------------------------------------------------------------------------


async def test_routes_are_detached_not_deleted(
    async_client: AsyncClient, test_session: AsyncSession, test_route: Any
) -> None:
    """Deleting the driver must not take their delivery history with it; the
    route survives unassigned (`driver_id SET NULL`)."""
    driver_json = await _initialize_driver(async_client)
    test_route.driver_id = UUID(driver_json["driver_id"])
    # Assigning a driver means the route is scheduled (ck_routes_assigned_
    # route_has_start_time), so the start time has to travel with it.
    test_route.start_time = time(8, 0)
    await test_session.commit()

    with patch("firebase_admin.auth.delete_user"):
        assert (
            await async_client.delete(f"/drivers/{driver_json['driver_id']}")
        ).status_code == 204

    await test_session.refresh(test_route)
    assert test_route.driver_id is None


# ---------------------------------------------------------------------------
# The delete is admin-only
# ---------------------------------------------------------------------------


async def test_delete_requires_admin(
    client_with_overrides: Any, test_session: AsyncSession, async_client: AsyncClient
) -> None:
    """A driver cannot delete themselves (or anyone else)."""
    from fastapi import HTTPException, status

    from app.dependencies.auth import require_admin

    driver_json = await _initialize_driver(async_client)

    def deny_admin() -> bool:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    non_admin_client = await client_with_overrides({require_admin: deny_admin})

    with patch("firebase_admin.auth.delete_user") as delete_firebase_user:
        response = await non_admin_client.delete(f"/drivers/{driver_json['driver_id']}")

    assert response.status_code == 403
    delete_firebase_user.assert_not_called()
    survivors = (
        (
            await test_session.execute(
                select(Driver).where(Driver.driver_id == UUID(driver_json["driver_id"]))
            )
        )
        .scalars()
        .all()
    )
    assert len(survivors) == 1

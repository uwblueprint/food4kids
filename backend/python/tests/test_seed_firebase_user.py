"""Contract for ``ensure_firebase_user``: an existing account's password is
never written unless explicitly asked for (a password write signs out every
open session — see the function's own docstring).

Needs its own file because test_seed_database.py patches the function out
wholesale to keep the seed tests offline.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.seed_database import ensure_firebase_user

UID = "seed-admin-1"
EMAIL = "admin1@f4k.dev"
PASSWORD = "test123"
FIRST, LAST = "Priya", "Raman"
FULL_NAME = f"{FIRST} {LAST}"
CLAIMS = {"role": "admin", "given_name": FIRST, "family_name": LAST}


class UserNotFoundError(Exception):
    """Stand-in for ``firebase_admin.auth.UserNotFoundError``."""


# ``None`` is a meaningful value for ``custom_claims`` — it is what Firebase
# returns for an account that has never had any set — so it cannot double as
# "caller said nothing".
_IN_SYNC = object()


def _existing_user(
    *,
    email: str = EMAIL,
    display_name: str = FULL_NAME,
    email_verified: bool = True,
    custom_claims: Any = _IN_SYNC,
) -> MagicMock:
    """A ``UserRecord`` as the seed script reads it, already fully in sync."""
    record = MagicMock()
    record.email = email
    record.display_name = display_name
    record.email_verified = email_verified
    record.custom_claims = CLAIMS if custom_claims is _IN_SYNC else custom_claims
    return record


@pytest.fixture
def auth_mock() -> Any:
    """Patch the ``auth`` module the seed script imported.

    ``get_user`` returns a fully in-sync account by default, so each test only
    has to state the one thing it wants to be out of sync.
    """
    with patch("app.seed_database.auth") as mock:
        mock.UserNotFoundError = UserNotFoundError
        mock.get_user.return_value = _existing_user()
        yield mock


def _run(**kwargs: Any) -> str:
    """Seed one account. The ``auth_mock`` fixture is what it talks to."""
    return ensure_firebase_user(
        uid=UID,
        email=EMAIL,
        password=PASSWORD,
        role="admin",
        first_name=FIRST,
        last_name=LAST,
        **kwargs,
    )


class TestExistingAccountKeepsItsPassword:
    """The regression that matters: re-seeding must not sign anyone out."""

    def test_password_is_not_written_when_the_account_exists(
        self, auth_mock: Any
    ) -> None:
        _run()

        for call in auth_mock.update_user.call_args_list:
            assert "password" not in call.kwargs, (
                "Writing the password revokes every outstanding token. The "
                "account already exists, so there is nothing to establish."
            )

    def test_an_in_sync_account_is_not_written_to_at_all(self, auth_mock: Any) -> None:
        """Nothing differs, so there is no reason to touch Firebase."""
        _run()

        auth_mock.update_user.assert_not_called()
        auth_mock.set_custom_user_claims.assert_not_called()
        auth_mock.create_user.assert_not_called()

    def test_a_drifted_field_is_written_without_the_password(
        self, auth_mock: Any
    ) -> None:
        """Reconciling other fields must not smuggle the password along."""
        auth_mock.get_user.return_value = _existing_user(display_name="Stale Name")

        _run()

        auth_mock.update_user.assert_called_once_with(UID, display_name=FULL_NAME)

    @pytest.mark.parametrize(
        ("drift", "expected"),
        [
            ({"email": "old@f4k.dev"}, {"email": EMAIL}),
            ({"display_name": "Old Name"}, {"display_name": FULL_NAME}),
            ({"email_verified": False}, {"email_verified": True}),
        ],
    )
    def test_only_the_field_that_drifted_is_written(
        self, auth_mock: Any, drift: dict[str, Any], expected: dict[str, Any]
    ) -> None:
        auth_mock.get_user.return_value = _existing_user(**drift)

        _run()

        auth_mock.update_user.assert_called_once_with(UID, **expected)

    def test_several_drifted_fields_are_written_in_one_call(
        self, auth_mock: Any
    ) -> None:
        auth_mock.get_user.return_value = _existing_user(
            email="old@f4k.dev", display_name="Old Name", email_verified=False
        )

        _run()

        auth_mock.update_user.assert_called_once_with(
            UID, email=EMAIL, display_name=FULL_NAME, email_verified=True
        )


class TestResetPasswordsIsOptIn:
    """The escape hatch, for a password that really has drifted."""

    def test_password_is_written_when_asked_for(self, auth_mock: Any) -> None:
        _run(reset_password=True)

        auth_mock.update_user.assert_called_once_with(UID, password=PASSWORD)

    def test_password_rides_along_with_other_drifted_fields(
        self, auth_mock: Any
    ) -> None:
        auth_mock.get_user.return_value = _existing_user(display_name="Old Name")

        _run(reset_password=True)

        auth_mock.update_user.assert_called_once_with(
            UID, display_name=FULL_NAME, password=PASSWORD
        )

    def test_default_is_off(self, auth_mock: Any) -> None:
        """Signing everyone out is never the default."""
        _run()

        auth_mock.update_user.assert_not_called()


class TestMissingAccountIsCreated:
    """A new account has no session to lose, so the password must be set."""

    @pytest.fixture
    def auth_mock(self, auth_mock: Any) -> Any:
        auth_mock.get_user.side_effect = UserNotFoundError()
        return auth_mock

    def test_created_with_the_seed_password(self, auth_mock: Any) -> None:
        _run()

        auth_mock.create_user.assert_called_once_with(
            uid=UID,
            email=EMAIL,
            password=PASSWORD,
            email_verified=True,
            display_name=FULL_NAME,
        )
        auth_mock.update_user.assert_not_called()

    def test_claims_are_set_on_creation(self, auth_mock: Any) -> None:
        """A new account has no claims, so the role has to be established."""
        _run()

        auth_mock.set_custom_user_claims.assert_called_once_with(UID, CLAIMS)

    def test_reset_password_changes_nothing_for_a_new_account(
        self, auth_mock: Any
    ) -> None:
        _run(reset_password=True)

        auth_mock.create_user.assert_called_once()
        auth_mock.update_user.assert_not_called()


class TestClaims:
    """Claims are reconciled like any other field. They do not revoke tokens,
    but writing them every run is pointless work against a rate-limited API."""

    def test_unchanged_claims_are_not_rewritten(self, auth_mock: Any) -> None:
        _run()

        auth_mock.set_custom_user_claims.assert_not_called()

    @pytest.mark.parametrize(
        "stale",
        [
            {"role": "driver", "given_name": FIRST, "family_name": LAST},
            {"role": "admin", "given_name": "Someone", "family_name": LAST},
            {"role": "admin"},
            {},
            None,
        ],
    )
    def test_stale_or_absent_claims_are_rewritten(
        self, auth_mock: Any, stale: dict[str, Any] | None
    ) -> None:
        """A wrong role is a security-relevant drift, and ``None`` is what
        Firebase returns for an account that has never had claims set."""
        auth_mock.get_user.return_value = _existing_user(custom_claims=stale)

        _run()

        auth_mock.set_custom_user_claims.assert_called_once_with(UID, CLAIMS)

    def test_claims_are_written_even_when_no_other_field_drifted(
        self, auth_mock: Any
    ) -> None:
        auth_mock.get_user.return_value = _existing_user(custom_claims={})

        _run()

        auth_mock.update_user.assert_not_called()
        auth_mock.set_custom_user_claims.assert_called_once_with(UID, CLAIMS)


class TestReturnValue:
    @pytest.mark.usefixtures("auth_mock")
    def test_returns_the_uid_for_an_existing_account(self) -> None:
        assert _run() == UID

    def test_returns_the_uid_for_a_created_account(self, auth_mock: Any) -> None:
        auth_mock.get_user.side_effect = UserNotFoundError()

        assert _run() == UID

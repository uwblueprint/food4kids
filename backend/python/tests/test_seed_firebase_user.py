"""Contract for ``sync_firebase_accounts``: an existing account's password is
never written unless explicitly asked for (a password write signs out every
open session — see the function's own docstring), and the whole account set is
reconciled from a single ``list_users`` sweep rather than a ``get_user`` each.

Needs its own file because test_seed_database.py patches the function out
wholesale to keep the seed tests offline.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import firebase_admin
import pytest

from app.seed_database import (
    SeedAccount,
    firebase_account_snapshot,
    make_seed_account,
    seed_account_name,
    sync_firebase_accounts,
)

UID = "seed-admin-1"
EMAIL = "admin1@f4k.dev"
PASSWORD = "test123"
FIRST, LAST = "Priya", "Raman"
FULL_NAME = f"{FIRST} {LAST}"
CLAIMS = {"role": "admin", "given_name": FIRST, "family_name": LAST}

ACCOUNT = SeedAccount(
    uid=UID, email=EMAIL, role="admin", first_name=FIRST, last_name=LAST
)


# ``None`` is a meaningful value for ``custom_claims`` — it is what Firebase
# returns for an account that has never had any set — so it cannot double as
# "caller said nothing".
_IN_SYNC = object()


def _existing_user(
    *,
    uid: str = UID,
    email: str = EMAIL,
    display_name: str = FULL_NAME,
    email_verified: bool = True,
    custom_claims: Any = _IN_SYNC,
) -> MagicMock:
    """A ``UserRecord`` as the seed script reads it, already fully in sync."""
    record = MagicMock()
    record.uid = uid
    record.email = email
    record.display_name = display_name
    record.email_verified = email_verified
    record.custom_claims = CLAIMS if custom_claims is _IN_SYNC else custom_claims
    return record


@pytest.fixture
def auth_mock() -> Any:
    """Patch the ``auth`` module the seed script imported.

    ``list_users`` returns one fully in-sync account by default, so each test
    only has to state the one thing it wants to be out of sync.
    """
    with patch("app.seed_database.auth") as mock:
        mock.list_users.return_value.iterate_all.return_value = [_existing_user()]
        yield mock


def _run(accounts: list[SeedAccount] | None = None, **kwargs: Any) -> None:
    """Sync one account by default, against the sweep ``auth_mock`` returns."""
    sync_firebase_accounts(
        [ACCOUNT] if accounts is None else accounts,
        firebase_account_snapshot(),
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
        auth_mock.list_users.return_value.iterate_all.return_value = [
            _existing_user(display_name="Stale Name")
        ]

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
        auth_mock.list_users.return_value.iterate_all.return_value = [
            _existing_user(**drift)
        ]

        _run()

        auth_mock.update_user.assert_called_once_with(UID, **expected)

    def test_several_drifted_fields_are_written_in_one_call(
        self, auth_mock: Any
    ) -> None:
        auth_mock.list_users.return_value.iterate_all.return_value = [
            _existing_user(
                email="old@f4k.dev", display_name="Old Name", email_verified=False
            )
        ]

        _run()

        auth_mock.update_user.assert_called_once_with(
            UID, email=EMAIL, display_name=FULL_NAME, email_verified=True
        )


class TestResetPasswordsIsOptIn:
    """The escape hatch, for a password that really has drifted."""

    def test_password_is_written_when_asked_for(self, auth_mock: Any) -> None:
        _run(reset_passwords=True)

        auth_mock.update_user.assert_called_once_with(UID, password=PASSWORD)

    def test_password_rides_along_with_other_drifted_fields(
        self, auth_mock: Any
    ) -> None:
        auth_mock.list_users.return_value.iterate_all.return_value = [
            _existing_user(display_name="Old Name")
        ]

        _run(reset_passwords=True)

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
        auth_mock.list_users.return_value.iterate_all.return_value = []
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

    def test_reset_passwords_changes_nothing_for_a_new_account(
        self, auth_mock: Any
    ) -> None:
        _run(reset_passwords=True)

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
        auth_mock.list_users.return_value.iterate_all.return_value = [
            _existing_user(custom_claims=stale)
        ]

        _run()

        auth_mock.set_custom_user_claims.assert_called_once_with(UID, CLAIMS)

    def test_claims_are_written_even_when_no_other_field_drifted(
        self, auth_mock: Any
    ) -> None:
        auth_mock.list_users.return_value.iterate_all.return_value = [
            _existing_user(custom_claims={})
        ]

        _run()

        auth_mock.update_user.assert_not_called()
        auth_mock.set_custom_user_claims.assert_called_once_with(UID, CLAIMS)


class TestOneSweepForTheWholeAccountSet:
    """The speed fix: N accounts cost one read, not N reads."""

    def _accounts(self, count: int) -> list[SeedAccount]:
        return [
            SeedAccount(
                uid=f"seed-driver-{i:03d}",
                email=f"driver{i:03d}@f4k.dev",
                role="driver",
                first_name=FIRST,
                last_name=LAST,
            )
            for i in range(count)
        ]

    def test_accounts_are_read_with_a_single_list_users_call(
        self, auth_mock: Any
    ) -> None:
        auth_mock.list_users.return_value.iterate_all.return_value = []

        _run(self._accounts(50))

        auth_mock.list_users.assert_called_once_with()
        auth_mock.get_user.assert_not_called()

    def test_every_missing_account_is_created(self, auth_mock: Any) -> None:
        auth_mock.list_users.return_value.iterate_all.return_value = []

        _run(self._accounts(50))

        created = {call.kwargs["uid"] for call in auth_mock.create_user.call_args_list}
        assert created == {f"seed-driver-{i:03d}" for i in range(50)}

    def test_accounts_outside_the_seed_set_are_left_alone(self, auth_mock: Any) -> None:
        """The sweep returns the whole project, including real developer
        accounts. Anything the seed does not own must not be touched."""
        auth_mock.list_users.return_value.iterate_all.return_value = [
            _existing_user(uid="a-real-person", email="colin@f4k.dev"),
            _existing_user(),
        ]

        _run()

        auth_mock.update_user.assert_not_called()
        auth_mock.create_user.assert_not_called()
        auth_mock.set_custom_user_claims.assert_not_called()

    def test_a_failed_write_propagates(self, auth_mock: Any) -> None:
        """A write running on the pool must not fail silently."""
        auth_mock.list_users.return_value.iterate_all.return_value = []
        auth_mock.create_user.side_effect = RuntimeError("firebase said no")

        with pytest.raises(RuntimeError, match="firebase said no"):
            _run()


class TestNamesAreDerivedFromTheUid:
    """Random names per run made every re-seed a full rewrite of every
    account. The name is now a function of the uid, so a re-seed is a no-op."""

    def test_the_same_uid_always_gets_the_same_name(self) -> None:
        assert seed_account_name("seed-driver-001") == seed_account_name(
            "seed-driver-001"
        )

    def test_different_uids_get_different_names(self) -> None:
        names = {seed_account_name(f"seed-driver-{i:03d}") for i in range(50)}
        assert len(names) > 1, "every account would be named the same person"

    def test_make_seed_account_carries_the_derived_name(self) -> None:
        account = make_seed_account(
            uid="seed-driver-007", email="driver007@f4k.dev", role="driver"
        )

        assert (account.first_name, account.last_name) == seed_account_name(
            "seed-driver-007"
        )
        assert account.display_name == f"{account.first_name} {account.last_name}"
        assert account.claims == {
            "role": "driver",
            "given_name": account.first_name,
            "family_name": account.last_name,
        }

    def test_deriving_a_name_does_not_disturb_the_seed_random_stream(self) -> None:
        """The names come off a separate generator, so adding an account
        cannot reshuffle every other seeded field."""
        from app.seed_database import fake

        fake.seed_instance(1234)
        before = [fake.sentence() for _ in range(5)]

        fake.seed_instance(1234)
        seed_account_name("seed-driver-001")
        after = [fake.sentence() for _ in range(5)]

        assert before == after


class TestRateLimitedWritesAreRetried:
    """Firebase rate-limits account writes per project, so a run that has to
    write every account at once expects to be told to slow down."""

    @pytest.fixture(autouse=True)
    def _no_backoff_sleep(self) -> Any:
        """The retry's own waits would otherwise make this suite take seconds."""
        with patch("app.seed_database.time_module.sleep") as sleep:
            yield sleep

    @staticmethod
    def _quota_error() -> firebase_admin.exceptions.FirebaseError:
        return firebase_admin.exceptions.InvalidArgumentError(
            "Error while calling Auth service (QUOTA_EXCEEDED)."
        )

    def test_a_quota_error_is_retried_until_it_succeeds(
        self, auth_mock: Any, _no_backoff_sleep: Any
    ) -> None:
        auth_mock.list_users.return_value.iterate_all.return_value = []
        auth_mock.create_user.side_effect = [self._quota_error(), None]

        _run()

        assert auth_mock.create_user.call_count == 2
        _no_backoff_sleep.assert_called_once()

    def test_backoff_doubles_between_attempts(
        self, auth_mock: Any, _no_backoff_sleep: Any
    ) -> None:
        auth_mock.list_users.return_value.iterate_all.return_value = []
        auth_mock.create_user.side_effect = [self._quota_error()] * 3 + [None]

        _run()

        waited = [call.args[0] for call in _no_backoff_sleep.call_args_list]
        assert waited == [1.0, 2.0, 4.0]

    def test_a_quota_error_that_never_clears_fails_the_seed(
        self, auth_mock: Any
    ) -> None:
        auth_mock.list_users.return_value.iterate_all.return_value = []
        auth_mock.create_user.side_effect = self._quota_error()

        with pytest.raises(firebase_admin.exceptions.FirebaseError):
            _run()

        assert auth_mock.create_user.call_count == 5

    def test_the_create_retry_still_goes_on_to_set_the_claims(
        self, auth_mock: Any
    ) -> None:
        """Waiting out the rate limit must not lose the rest of the write."""
        auth_mock.list_users.return_value.iterate_all.return_value = []
        auth_mock.create_user.side_effect = [self._quota_error(), None]

        _run()

        auth_mock.set_custom_user_claims.assert_called_once_with(UID, CLAIMS)

    def test_a_quota_error_on_the_claims_call_does_not_re_create_the_account(
        self, auth_mock: Any, _no_backoff_sleep: Any
    ) -> None:
        """The interleaving a cold seed actually hits: the account is created,
        then the *claims* call is the one the rate limit lands on. Retrying the
        create as well would call ``create_user`` for a uid that now exists,
        which raises ``UidAlreadyExistsError`` — a ``FirebaseError`` carrying no
        "QUOTA_EXCEEDED", so the backoff would re-raise it and fail the seed."""
        auth_mock.list_users.return_value.iterate_all.return_value = []
        auth_mock.set_custom_user_claims.side_effect = [self._quota_error(), None]

        _run()

        auth_mock.create_user.assert_called_once()
        assert [c.args for c in auth_mock.set_custom_user_claims.call_args_list] == [
            (UID, CLAIMS),
            (UID, CLAIMS),
        ]
        _no_backoff_sleep.assert_called_once()

    def test_a_quota_error_on_the_claims_call_does_not_rewrite_a_drifted_field(
        self, auth_mock: Any
    ) -> None:
        """Same shape for an existing account: the ``update_user`` half has
        landed, so only the claims call is retried."""
        auth_mock.list_users.return_value.iterate_all.return_value = [
            _existing_user(display_name="Stale Name", custom_claims=None)
        ]
        auth_mock.set_custom_user_claims.side_effect = [self._quota_error(), None]

        _run()

        auth_mock.update_user.assert_called_once_with(UID, display_name=FULL_NAME)
        assert auth_mock.set_custom_user_claims.call_count == 2

    def test_a_claims_quota_error_that_never_clears_fails_the_seed(
        self, auth_mock: Any
    ) -> None:
        """Resuming is not the same as giving up on the failure."""
        auth_mock.list_users.return_value.iterate_all.return_value = []
        auth_mock.set_custom_user_claims.side_effect = self._quota_error()

        with pytest.raises(firebase_admin.exceptions.FirebaseError):
            _run()

        auth_mock.create_user.assert_called_once()
        assert auth_mock.set_custom_user_claims.call_count == 5

    def test_any_other_firebase_error_fails_immediately(self, auth_mock: Any) -> None:
        """Only the rate limit is a wait; everything else is a real failure."""
        auth_mock.list_users.return_value.iterate_all.return_value = []
        auth_mock.create_user.side_effect = firebase_admin.exceptions.NotFoundError(
            "no such project"
        )

        with pytest.raises(firebase_admin.exceptions.NotFoundError):
            _run()

        auth_mock.create_user.assert_called_once()


class TestTheSweepBelongsToTheCaller:
    """One sweep serves the whole run — admins and drivers are synced
    separately, and neither call may go back to Firebase to re-read."""

    def test_sync_never_reads_accounts_itself(self, auth_mock: Any) -> None:
        sync_firebase_accounts([ACCOUNT], {})

        auth_mock.list_users.assert_not_called()
        auth_mock.get_user.assert_not_called()

    def test_an_empty_snapshot_means_everything_is_created(
        self, auth_mock: Any
    ) -> None:
        sync_firebase_accounts([ACCOUNT], {})

        auth_mock.create_user.assert_called_once()

    def test_a_snapshot_entry_is_reconciled_rather_than_created(
        self, auth_mock: Any
    ) -> None:
        sync_firebase_accounts([ACCOUNT], {UID: _existing_user()})

        auth_mock.create_user.assert_not_called()
        auth_mock.update_user.assert_not_called()

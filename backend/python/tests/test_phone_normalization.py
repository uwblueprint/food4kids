"""Phone numbers normalize to RFC 3966 on every write path.

The format matters because E.164 has no extension field — it parsed
``(519) 576-3443 Ext. 1`` and returned ``+15195763443``, dropping the extension
with nothing raised. F4K's office number has one and school locations routinely
do, so the stored form is RFC 3966 (``tel:+1-519-576-3443;ext=1``).
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.admin import AdminUpdate
from app.models.driver import DriverUpdate
from app.models.location import LocationCreate
from app.utilities.utils import MAX_STORED_PHONE_LENGTH, validate_phone

# Every spelling of the same Kitchener number an admin might paste or a
# spreadsheet might hold.
EQUIVALENT_SPELLINGS = [
    "+15195763443",
    "15195763443",
    "5195763443",
    "519-576-3443",
    "519 576 3443",
    "(519) 576-3443",
    "(519)576-3443",
    "519.576.3443",
    "+1 (519) 576-3443",
    "tel:+1-519-576-3443",
]

EXTENSION_SPELLINGS = [
    "(519) 576-3443 Ext. 1",
    "(519) 576-3443 ext 1",
    "(519) 576-3443 x1",
    "519-576-3443 extension 1",
    "tel:+1-519-576-3443;ext=1",
]

INVALID = [
    "a",
    "",
    "   ",
    "123",
    "555-1234",
    "(555) 123-4567",  # 555 is not a real area code
    "+1 000 000 0000",
    "not a phone at all",
    "519-576-344",  # one digit short
    "519-576-34433",  # one digit long
]


class TestValidatePhone:
    @pytest.mark.parametrize("value", EQUIVALENT_SPELLINGS)
    def test_spellings_collapse_to_one_stored_form(self, value: str) -> None:
        assert validate_phone(value) == "tel:+1-519-576-3443"

    @pytest.mark.parametrize("value", EXTENSION_SPELLINGS)
    def test_extension_survives(self, value: str) -> None:
        assert validate_phone(value) == "tel:+1-519-576-3443;ext=1"

    def test_multi_digit_extension_survives(self) -> None:
        assert validate_phone("(519) 576-3443 ext. 224") == (
            "tel:+1-519-576-3443;ext=224"
        )

    def test_normalization_is_idempotent(self) -> None:
        once = validate_phone("(519) 576-3443 Ext. 1")
        assert validate_phone(once) == once

    def test_stored_form_is_a_usable_tel_uri(self) -> None:
        """The call button uses the column value directly as an href."""
        assert validate_phone("(519) 576-3443").startswith("tel:+")

    @pytest.mark.parametrize("value", INVALID)
    def test_invalid_numbers_raise(self, value: str) -> None:
        with pytest.raises(ValueError):
            validate_phone(value)

    def test_longest_accepted_form_fits_the_column(self) -> None:
        """drivers.phone is VARCHAR(32); nothing valid may exceed it."""
        longest = validate_phone("(519) 576-3443 ext. 9999999")
        assert len(longest) <= 32

    def test_extension_that_overflows_the_column_is_rejected(self) -> None:
        """The cap is on the *normalized* value, not the submitted string.

        This input is 32 characters raw — a ``Field(max_length=32)`` would wave
        it through, and it would then be a Postgres "value too long" error at
        commit rather than a 422.
        """
        raw = "519 576 3443 ext 123456789012345"
        assert len(raw) == MAX_STORED_PHONE_LENGTH
        with pytest.raises(ValueError, match="too long to store"):
            validate_phone(raw)

    def test_driver_update_rejects_an_overflowing_extension(self) -> None:
        """DriverUpdate.phone carries no max_length, so the cap in
        validate_phone is the only thing standing between a long extension and
        the varchar(32) column."""
        with pytest.raises(ValidationError):
            DriverUpdate(phone="519 576 3443 ext 123456789012345")


def _location(**overrides: object) -> LocationCreate:
    return LocationCreate.model_validate(
        {
            "location_group_id": uuid4(),
            "name": "Central Elementary",
            "contact_name": "Jane Smith",
            "address": "123 Main St, Kitchener",
            "phone_primary": "(519) 576-3443",
            "delivery_type": "School",
            **overrides,
        }
    )


class TestLocationCreateNormalizes:
    """A household is created and replaced, never edited, so LocationCreate is
    the only model that writes its phone numbers."""

    def test_normalizes_both_numbers(self) -> None:
        location = _location(phone_secondary="519.284.2498 ext. 12")
        assert location.phone_primary == "tel:+1-519-576-3443"
        assert location.phone_secondary == "tel:+1-519-284-2498;ext=12"

    def test_leaves_secondary_none(self) -> None:
        assert _location().phone_secondary is None

    def test_rejects_invalid_primary(self) -> None:
        with pytest.raises(ValidationError):
            _location(phone_primary="nope")

    def test_rejects_invalid_secondary(self) -> None:
        with pytest.raises(ValidationError):
            _location(phone_secondary="nope")


class TestUpdateModelsNormalize:
    """Update models must normalize too.

    ``update_*_by_id`` assigns straight onto the ORM row, and SQLModel table
    instances don't re-run validators on assignment — so a missing validator
    here means an edit writes the raw client string and the value renders
    unformatted next to properly stored ones. Locations have no update model:
    a household is created and replaced, never edited in place.
    """

    def test_driver_update_normalizes(self) -> None:
        assert DriverUpdate(phone="(519) 576-3443").phone == "tel:+1-519-576-3443"

    def test_driver_update_rejects_invalid(self) -> None:
        with pytest.raises(ValidationError):
            DriverUpdate(phone="a")

    def test_driver_update_omitting_phone_is_unchanged(self) -> None:
        assert DriverUpdate(first_name="Emily").phone is None

    def test_admin_update_normalizes(self) -> None:
        update = AdminUpdate(admin_phone="519 576 3443 x2")
        assert update.admin_phone == "tel:+1-519-576-3443;ext=2"

    def test_admin_update_rejects_invalid(self) -> None:
        with pytest.raises(ValidationError):
            AdminUpdate(admin_phone="555-1234")


class TestUpdateModelsRejectExplicitNull:
    """A non-nullable phone column must reject an explicit ``null``.

    The ``None`` default means "field omitted" and never reaches a validator,
    so a client sending ``{"admin_phone": null}`` would otherwise assign None
    onto the row and fail as an IntegrityError at commit — a 500 — instead of
    a 422 naming the field.
    """

    def test_admin_update_rejects_null_phone(self) -> None:
        with pytest.raises(ValidationError):
            AdminUpdate(admin_phone=None)

    def test_admin_update_still_allows_omitting_phone(self) -> None:
        assert AdminUpdate(first_name="Emily").admin_phone is None

    def test_driver_update_rejects_null_phone(self) -> None:
        with pytest.raises(ValidationError):
            DriverUpdate(phone=None)

"""Phone numbers normalize to RFC 3966 on every write path.

The format matters because E.164 has no extension field — it parsed
``(519) 576-3443 Ext. 1`` and returned ``+15195763443``, dropping the extension
with nothing raised. F4K's office number has one and school locations routinely
do, so the stored form is RFC 3966 (``tel:+1-519-576-3443;ext=1``).
"""

import pytest
from pydantic import ValidationError

from app.models.admin import AdminUpdate
from app.models.driver import DriverUpdate
from app.models.location import LocationUpdate
from app.utilities.utils import validate_phone

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


class TestUpdateModelsNormalize:
    """Update models must normalize too.

    ``update_*_by_id`` assigns straight onto the ORM row, and SQLModel table
    instances don't re-run validators on assignment — so a missing validator
    here means an edit writes the raw client string and the value renders
    unformatted next to properly stored ones.
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

    def test_location_update_normalizes_both_numbers(self) -> None:
        update = LocationUpdate(
            phone_primary="(519) 576-3443",
            phone_secondary="519.284.2498 ext. 12",
        )
        assert update.phone_primary == "tel:+1-519-576-3443"
        assert update.phone_secondary == "tel:+1-519-284-2498;ext=12"

    def test_location_update_leaves_secondary_none(self) -> None:
        update = LocationUpdate(phone_primary="(519) 576-3443")
        assert update.phone_secondary is None

    def test_location_update_rejects_invalid_secondary(self) -> None:
        with pytest.raises(ValidationError):
            LocationUpdate(phone_primary="(519) 576-3443", phone_secondary="nope")

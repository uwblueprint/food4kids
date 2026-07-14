"""Tests for location import validation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.location import (
    AlertCode,
    DuplicateMatchField,
    Location,
    LocationImportEntry,
)
from app.services.implementations.location_import_validation import (
    collect_field_alerts,
    duplicate_matching_fields,
    entry_match_key,
    find_duplicate_index_groups,
    is_invalid_school_or_last_name,
    is_same_location,
    location_match_key,
    match_score,
    matching_fields,
    rows_are_duplicates,
)
from app.services.implementations.location_service import LocationService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def _entry(
    *,
    contact_name: str | None = "Smith",
    address: str | None = "123 Main St",
    phone_primary: str | None = "+15195551234",
    delivery_group: str | None = "Tuesday A",
) -> LocationImportEntry:
    return LocationImportEntry(
        contact_name=contact_name,
        address=address,
        delivery_group=delivery_group,
        phone_primary=phone_primary,
    )


class TestFieldValidation:
    def test_missing_each_required_field(self) -> None:
        assert collect_field_alerts(
            _entry(contact_name=None),
            geocode_ok=True,
            phone_invalid=False,
        ) == [AlertCode.MISSING_NAME]

        assert collect_field_alerts(
            _entry(address=None),
            geocode_ok=None,
            phone_invalid=False,
        ) == [AlertCode.MISSING_ADDRESS]

        assert collect_field_alerts(
            _entry(phone_primary=None),
            geocode_ok=True,
            phone_invalid=False,
        ) == [AlertCode.MISSING_PHONE_NUMBER]

        assert collect_field_alerts(
            _entry(delivery_group=None),
            geocode_ok=True,
            phone_invalid=False,
        ) == [AlertCode.MISSING_DELIVERY_GROUP]

    def test_invalid_school_or_last_name_all_digits(self) -> None:
        assert is_invalid_school_or_last_name("33333333") is True
        assert is_invalid_school_or_last_name("Smith") is False
        assert is_invalid_school_or_last_name("Smith2") is False

        alerts = collect_field_alerts(
            _entry(contact_name="33333333"),
            geocode_ok=True,
            phone_invalid=False,
        )
        assert AlertCode.INVALID_NAME in alerts

    def test_invalid_address_when_geocode_fails(self) -> None:
        alerts = collect_field_alerts(
            _entry(address="95 Roger"),
            geocode_ok=False,
            phone_invalid=False,
        )
        assert alerts == [AlertCode.INVALID_ADDRESS]

    def test_invalid_phone_number(self) -> None:
        alerts = collect_field_alerts(
            _entry(),
            geocode_ok=True,
            phone_invalid=True,
        )
        assert AlertCode.INVALID_PHONE_NUMBER in alerts

    def test_invalid_phone_secondary(self) -> None:
        alerts = collect_field_alerts(
            LocationImportEntry(
                contact_name="Smith",
                address="123 Main St",
                delivery_group="Tuesday A",
                phone_primary="+15195551234",
                phone_secondary="not-a-phone",
            ),
            geocode_ok=True,
            phone_invalid=False,
            phone_secondary_invalid=True,
        )
        assert AlertCode.INVALID_PHONE_NUMBER in alerts

    def test_multiple_errors_on_one_row(self) -> None:
        alerts = collect_field_alerts(
            _entry(contact_name="33333333", delivery_group=None),
            geocode_ok=True,
            phone_invalid=False,
        )
        assert AlertCode.INVALID_NAME in alerts
        assert AlertCode.MISSING_DELIVERY_GROUP in alerts


class TestDuplicateDetection:
    def test_three_of_three_is_duplicate(self) -> None:
        left = _entry(
            contact_name="Chan",
            address="105 Albert St",
            phone_primary="+15192842498",
        )
        right = _entry(
            contact_name="Chan",
            address="105 Albert St",
            phone_primary="+15192842498",
        )
        assert rows_are_duplicates(left, right)

    def test_name_and_phone_two_of_three(self) -> None:
        left = _entry(
            contact_name="Bale",
            address="10 First Ave",
            phone_primary="+14272842498",
        )
        right = _entry(
            contact_name="Bale",
            address="20 Second Ave",
            phone_primary="+14272842498",
        )
        assert rows_are_duplicates(left, right)

    def test_address_and_phone_two_of_three(self) -> None:
        left = _entry(
            contact_name="Wang",
            address="80 Mooregate Cres",
            phone_primary="+15193034390",
        )
        right = _entry(
            contact_name="Loren",
            address="80 Mooregate Cres",
            phone_primary="+15193034390",
        )
        assert rows_are_duplicates(left, right)

    def test_name_and_address_two_of_three(self) -> None:
        left = _entry(
            contact_name="Weber",
            address="527 Parkside Dr",
            phone_primary="+15191111111",
        )
        right = _entry(
            contact_name="Weber",
            address="527 Parkside Dr",
            phone_primary="+15192222222",
        )
        assert rows_are_duplicates(left, right)

    def test_one_of_three_address_only_not_duplicate(self) -> None:
        left = _entry(
            contact_name="Family A",
            address="100 Shared Building",
            phone_primary="+15191111111",
        )
        right = _entry(
            contact_name="Family B",
            address="100 Shared Building",
            phone_primary="+15192222222",
        )
        assert duplicate_matching_fields(left, right) == [DuplicateMatchField.ADDRESS]
        assert not rows_are_duplicates(left, right)

    def test_one_of_three_phone_only_not_duplicate(self) -> None:
        left = _entry(
            contact_name="Family A",
            address="1 A St",
            phone_primary="+15193034390",
        )
        right = _entry(
            contact_name="Family B",
            address="2 B St",
            phone_primary="+15193034390",
        )
        assert not rows_are_duplicates(left, right)

    def test_one_of_three_name_only_not_duplicate(self) -> None:
        left = _entry(
            contact_name="Smith",
            address="1 A St",
            phone_primary="+15191111111",
        )
        right = _entry(
            contact_name="Smith",
            address="2 B St",
            phone_primary="+15192222222",
        )
        assert not rows_are_duplicates(left, right)

    def test_different_address_formatting_not_duplicate(self) -> None:
        left = _entry(
            address="123 Main St",
            phone_primary="+15195551274",
        )
        right = _entry(
            address="123 Main Street",
            phone_primary="+15195551234",
        )
        assert not rows_are_duplicates(left, right)

    def test_name_match_is_case_insensitive(self) -> None:
        left = _entry(contact_name="Smith")
        right = _entry(contact_name="smith")
        assert rows_are_duplicates(left, right)

    def test_address_match_is_case_insensitive(self) -> None:
        left = _entry(address="123 Main St")
        right = _entry(address="123 main st")
        assert rows_are_duplicates(left, right)

    def test_transitive_duplicate_cluster(self) -> None:
        entries = [
            _entry(
                contact_name="Alpha",
                address="1 A St",
                phone_primary="+15191111111",
            ),
            _entry(
                contact_name="Alpha",
                address="2 B St",
                phone_primary="+15191111111",
            ),
            _entry(
                contact_name="Gamma",
                address="2 B St",
                phone_primary="+15191111111",
            ),
        ]
        groups = find_duplicate_index_groups(entries)
        assert groups == [[0, 1, 2]]

    def test_all_members_in_duplicate_group(self) -> None:
        entries = [
            _entry(contact_name="A", address="1 St", phone_primary="+15191111111"),
            _entry(contact_name="A", address="2 St", phone_primary="+15191111111"),
        ]
        groups = find_duplicate_index_groups(entries)
        assert groups == [[0, 1]]


class TestMatchKey:
    """The same key function serves in-file dedup and entry-vs-Location matching."""

    def _location(
        self,
        *,
        contact_name: str = "Smith",
        address: str = "123 Main St",
        phone_primary: str = "+15195551234",
    ) -> Location:
        return Location(
            location_group_id=uuid4(),
            name=contact_name,
            contact_name=contact_name,
            address=address,
            phone_primary=phone_primary,
            delivery_type="Family",
        )

    def test_internal_whitespace_collapses(self) -> None:
        left = entry_match_key(_entry(contact_name="John  Smith"))
        right = entry_match_key(_entry(contact_name="John Smith"))
        assert left.name == right.name

    def test_blank_fields_never_match(self) -> None:
        left = entry_match_key(
            _entry(contact_name="  ", address="1 A St", phone_primary=None)
        )
        right = entry_match_key(
            _entry(contact_name="", address="2 B St", phone_primary=None)
        )
        assert left.name is None
        assert left.phone is None
        assert match_score(left, right) == 0

    def test_location_matches_entry_through_same_key(self) -> None:
        entry_key = entry_match_key(
            _entry(contact_name="smith", address="123  MAIN st")
        )
        location_key = location_match_key(self._location())
        assert matching_fields(entry_key, location_key) == [
            DuplicateMatchField.NAME,
            DuplicateMatchField.ADDRESS,
            DuplicateMatchField.PHONE,
        ]
        assert is_same_location(entry_key, location_key)

    def test_location_one_field_match_is_not_same(self) -> None:
        entry_key = entry_match_key(
            _entry(
                contact_name="Jones",
                address="99 Elsewhere Rd",
                phone_primary="+15195551234",
            )
        )
        location_key = location_match_key(self._location())
        assert match_score(entry_key, location_key) == 1
        assert not is_same_location(entry_key, location_key)


class TestExistingGeocodedAddresses:
    @pytest.mark.asyncio
    async def test_returns_exact_matches_with_coordinates(
        self, test_session: AsyncSession, test_location_group: Any
    ) -> None:
        known = "123 Main St, City, State 12345"
        unknown = "999 New Ave"
        ungeocoded = "No Coords Rd"

        test_session.add(
            Location(
                location_group_id=test_location_group.location_group_id,
                name="Known",
                contact_name="Known",
                delivery_type="Family",
                address=known,
                phone_primary="+15195551234",
                longitude=-80.5,
                latitude=43.4,
            )
        )
        test_session.add(
            Location(
                location_group_id=test_location_group.location_group_id,
                name="Bare",
                contact_name="Bare",
                delivery_type="Family",
                address=ungeocoded,
                phone_primary="+15195551235",
                longitude=None,
                latitude=None,
            )
        )
        await test_session.flush()

        service = LocationService(
            logging.getLogger("test"),
            MagicMock(),
            MagicMock(),
        )
        result = await service._existing_geocoded_addresses(
            test_session, {known, unknown, ungeocoded}
        )
        assert result == {known}

    @pytest.mark.asyncio
    async def test_empty_input_returns_empty(self, test_session: AsyncSession) -> None:
        service = LocationService(
            logging.getLogger("test"),
            MagicMock(),
            MagicMock(),
        )
        assert await service._existing_geocoded_addresses(test_session, set()) == set()

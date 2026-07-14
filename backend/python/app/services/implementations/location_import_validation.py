"""Pure validation helpers for the location import review step."""

from __future__ import annotations

from typing import NamedTuple, TypeGuard

from app.models.location import (
    AlertCode,
    DuplicateMatchField,
    Location,
    LocationImportEntry,
)
from app.utilities.utils import validate_phone


def is_blank(value: str | None) -> bool:
    return value is None or not value.strip()


def present_str(value: str | None) -> TypeGuard[str]:
    """True when value is a non-empty string after stripping."""
    return value is not None and bool(value.strip())


def is_invalid_school_or_last_name(name: str) -> bool:
    """True when the name is present but all digits (e.g. '33333333')."""
    stripped = name.strip()
    return bool(stripped) and stripped.isdigit()


def try_normalize_phone(phone: str | None) -> tuple[str | None, bool]:
    """Return (E.164 phone, is_invalid).

    is_invalid is True only when a non-empty value fails validation.
    """
    if not present_str(phone):
        return None, False
    try:
        return validate_phone(phone), False
    except ValueError:
        return None, True


def collect_field_alerts(
    entry: LocationImportEntry,
    *,
    geocode_ok: bool | None,
    phone_invalid: bool,
    phone_secondary_invalid: bool = False,
) -> list[AlertCode]:
    """Collect per-field blocking alerts for one parsed import row."""
    alerts: list[AlertCode] = []

    if is_blank(entry.contact_name):
        alerts.append(AlertCode.MISSING_NAME)
    elif entry.contact_name is not None and is_invalid_school_or_last_name(
        entry.contact_name
    ):
        alerts.append(AlertCode.INVALID_NAME)

    if is_blank(entry.address):
        alerts.append(AlertCode.MISSING_ADDRESS)
    elif geocode_ok is False:
        alerts.append(AlertCode.INVALID_ADDRESS)

    if is_blank(entry.phone_primary):
        alerts.append(AlertCode.MISSING_PHONE_NUMBER)
    elif phone_invalid:
        alerts.append(AlertCode.INVALID_PHONE_NUMBER)

    if phone_secondary_invalid:
        alerts.append(AlertCode.INVALID_PHONE_NUMBER)

    if is_blank(entry.delivery_group):
        alerts.append(AlertCode.MISSING_DELIVERY_GROUP)

    return alerts


class MatchKey(NamedTuple):
    """Normalized (name, address, phone) key for the 2-of-3 duplicate rule.

    Blank fields normalize to None and never count as a match. Built from raw
    fields via match_key so import rows and existing Locations compare through
    the same normalization.
    """

    name: str | None
    address: str | None
    phone: str | None


def _text_match_key(value: str | None) -> str | None:
    """Casefold and collapse whitespace so formatting differences don't block a match."""
    if not present_str(value):
        return None
    return " ".join(value.casefold().split())


def _phone_match_key(phone: str | None) -> str | None:
    """Match key for phone_primary.

    Callers should normalize phones onto the entry before duplicate detection
    (see review_locations) so valid numbers compare as E.164.
    """
    if not present_str(phone):
        return None
    return phone.strip()


def match_key(
    contact_name: str | None,
    address: str | None,
    phone_primary: str | None,
) -> MatchKey:
    return MatchKey(
        name=_text_match_key(contact_name),
        address=_text_match_key(address),
        phone=_phone_match_key(phone_primary),
    )


def entry_match_key(entry: LocationImportEntry) -> MatchKey:
    return match_key(entry.contact_name, entry.address, entry.phone_primary)


def location_match_key(location: Location) -> MatchKey:
    return match_key(location.contact_name, location.address, location.phone_primary)


_MATCH_KEY_FIELDS = (
    DuplicateMatchField.NAME,
    DuplicateMatchField.ADDRESS,
    DuplicateMatchField.PHONE,
)


def matching_fields(left: MatchKey, right: MatchKey) -> list[DuplicateMatchField]:
    """Return the fields whose (non-blank) keys match between two rows."""
    return [
        field
        for field, left_value, right_value in zip(
            _MATCH_KEY_FIELDS, left, right, strict=True
        )
        if left_value is not None and left_value == right_value
    ]


def match_score(left: MatchKey, right: MatchKey) -> int:
    """Count how many of {name, address, phone} match between two keys."""
    return len(matching_fields(left, right))


def is_same_location(left: MatchKey, right: MatchKey) -> bool:
    """True when at least two of {name, address, phone} match (2-of-3 rule)."""
    return match_score(left, right) >= 2


def duplicate_matching_fields(
    left: LocationImportEntry,
    right: LocationImportEntry,
) -> list[DuplicateMatchField]:
    """Return fields that match between two rows for the 2-of-3 duplicate rule."""
    return matching_fields(entry_match_key(left), entry_match_key(right))


def rows_are_duplicates(
    left: LocationImportEntry,
    right: LocationImportEntry,
) -> bool:
    """True when at least two of {name, address, phone} match (2-of-3 rule)."""
    return is_same_location(entry_match_key(left), entry_match_key(right))


class _UnionFind:
    # This is a union-find data structure. It is used to find groups of duplicate rows.
    def __init__(self, size: int) -> None:
        self._parent = list(range(size))

    def find(self, node: int) -> int:
        while self._parent[node] != node:
            self._parent[node] = self._parent[self._parent[node]]
            node = self._parent[node]
        return node

    def union(self, left: int, right: int) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left != root_right:
            self._parent[root_right] = root_left


def find_duplicate_index_groups(
    entries: list[LocationImportEntry],
) -> list[list[int]]:
    """Return duplicate clusters as lists of 0-based indices (size >= 2).

    Transitive duplicates are merged via union-find (A~B and B~C => one group).
    Expects phone_primary to already be normalized when possible.
    """
    size = len(entries)
    if size < 2:
        return []

    keys = [entry_match_key(entry) for entry in entries]

    # Create a union-find data structure to find the connected components
    union_find = _UnionFind(size)
    for left in range(size):
        for right in range(left + 1, size):
            if is_same_location(keys[left], keys[right]):
                union_find.union(left, right)

    clusters: dict[int, list[int]] = {}
    for index in range(size):
        root = union_find.find(index)
        clusters.setdefault(root, []).append(index)

    return [sorted(indices) for indices in clusters.values() if len(indices) >= 2]

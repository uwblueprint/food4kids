"""Pure validation helpers for the location import review step."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeGuard

if TYPE_CHECKING:
    from collections.abc import Sequence

from app.models.location import AlertCode, LocationImportEntry
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
) -> list[AlertCode]:
    """Collect per-field blocking alerts for one parsed import row."""
    alerts: list[AlertCode] = []

    if is_blank(entry.contact_name):
        alerts.append(AlertCode.MISSING_SCHOOL_OR_LAST_NAME)
    elif present_str(entry.contact_name) and is_invalid_school_or_last_name(
        entry.contact_name
    ):
        alerts.append(AlertCode.INVALID_SCHOOL_OR_LAST_NAME)

    if is_blank(entry.address):
        alerts.append(AlertCode.MISSING_ADDRESS)
    elif geocode_ok is False:
        alerts.append(AlertCode.INVALID_ADDRESS)

    if is_blank(entry.phone_primary):
        alerts.append(AlertCode.MISSING_PHONE_NUMBER)
    elif phone_invalid:
        alerts.append(AlertCode.INVALID_PHONE_NUMBER)

    if is_blank(entry.delivery_group):
        alerts.append(AlertCode.MISSING_DELIVERY_GROUP)

    return alerts


def _name_match_key(name: str | None) -> str | None:
    if not present_str(name):
        return None
    return name.strip().casefold()


def _address_match_key(address: str | None) -> str | None:
    if not present_str(address):
        return None
    return address.strip()


def _phone_match_key(phone: str | None, normalized_phone: str | None) -> str | None:
    if normalized_phone:
        return normalized_phone
    if not present_str(phone):
        return None
    return phone.strip()


def count_duplicate_field_matches(
    left: LocationImportEntry,
    right: LocationImportEntry,
    *,
    left_phone: str | None,
    right_phone: str | None,
) -> int:
    """Count how many of {name, address, phone} match between two rows, which is the 2-of-3 rule"""
    matches = 0

    left_name = _name_match_key(left.contact_name)
    right_name = _name_match_key(right.contact_name)
    if left_name and right_name and left_name == right_name:
        matches += 1

    left_address = _address_match_key(left.address)
    right_address = _address_match_key(right.address)
    if left_address and right_address and left_address == right_address:
        matches += 1

    left_phone_key = _phone_match_key(left.phone_primary, left_phone)
    right_phone_key = _phone_match_key(right.phone_primary, right_phone)
    if left_phone_key and right_phone_key and left_phone_key == right_phone_key:
        matches += 1

    return matches


def rows_are_duplicates(
    left: LocationImportEntry,
    right: LocationImportEntry,
    *,
    left_phone: str | None,
    right_phone: str | None,
) -> bool:
    """True when at least two of {name, address, phone} match (2-of-3 rule)."""
    return (
        count_duplicate_field_matches(
            left,
            right,
            left_phone=left_phone,
            right_phone=right_phone,
        )
        >= 2
    )


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
    normalized_phones: Sequence[str | None],
) -> list[list[int]]:
    """Return duplicate clusters as lists of 0-based indices (size >= 2).

    Transitive duplicates are merged via union-find (A~B and B~C => one group).
    """
    size = len(entries)
    if size < 2:
        return []

    # Create a union-find data structure to find the connected components
    union_find = _UnionFind(size)
    for left in range(size):
        for right in range(left + 1, size):
            if rows_are_duplicates(
                entries[left],
                entries[right],
                left_phone=normalized_phones[left],
                right_phone=normalized_phones[right],
            ):
                union_find.union(left, right)

    clusters: dict[int, list[int]] = {}
    for index in range(size):
        root = union_find.find(index)
        clusters.setdefault(root, []).append(index)

    return [sorted(indices) for indices in clusters.values() if len(indices) >= 2]

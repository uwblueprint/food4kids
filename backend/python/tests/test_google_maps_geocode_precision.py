"""Tests for geocode precision detection.

The response fragments below are trimmed from real Google Geocoding API
responses for Waterloo Region addresses, so the predicate is exercised against
the shapes the API actually returns rather than invented ones.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.utilities.google_maps_client import is_precise_geocode_result


def _result(
    *,
    component_types: list[list[str]],
    location_type: str,
    types: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "address_components": [{"types": t} for t in component_types],
        "geometry": {"location_type": location_type, "location": {"lat": 0, "lng": 0}},
        "types": types or [],
        "formatted_address": "irrelevant",
        "place_id": "irrelevant",
    }


# (label, component types, location_type, result types)
PRECISE_CASES = [
    (
        "85 Church St, Kitchener — street address, interpolated",
        [["street_number"], ["route"], ["locality"], ["postal_code"]],
        "RANGE_INTERPOLATED",
        ["street_address"],
    ),
    (
        "200 University Ave W, Waterloo — named premise on a rooftop match",
        [["premise"], ["street_number"], ["route"], ["locality"]],
        "ROOFTOP",
        ["premise", "street_address"],
    ),
    (
        "375 King St N Apt 502, Waterloo — apartment subpremise",
        [["subpremise"], ["street_number"], ["route"], ["locality"]],
        "ROOFTOP",
        ["subpremise"],
    ),
    (
        "7091 Line 86, Wallenstein — rural civic address",
        [["street_number"], ["route"], ["locality"], ["postal_code"]],
        "RANGE_INTERPOLATED",
        ["street_address"],
    ),
    (
        "3585 Lobsinger Line, Heidelberg — rural rooftop match",
        [["street_number"], ["route"], ["locality"]],
        "ROOFTOP",
        ["street_address"],
    ),
]

IMPRECISE_CASES = [
    (
        "99999 Nonexistent Pkwy, Blandford Township — township centroid",
        [["administrative_area_level_3", "political"], ["administrative_area_level_2"]],
        "APPROXIMATE",
        ["administrative_area_level_3", "political"],
    ),
    (
        "Kitchener, ON — city only",
        [["locality", "political"], ["administrative_area_level_1"]],
        "APPROXIMATE",
        ["locality", "political"],
    ),
    (
        "King St, Waterloo — street with no number",
        [["route"], ["locality"], ["administrative_area_level_1"]],
        "GEOMETRIC_CENTER",
        ["route"],
    ),
    (
        "N2L 3G1 — postal code only",
        [["postal_code"], ["locality"], ["administrative_area_level_1"]],
        "APPROXIMATE",
        ["postal_code"],
    ),
    (
        "12 Maple Stret, Kitchner — typo, fell back to the city",
        [["locality", "political"], ["administrative_area_level_1"]],
        "APPROXIMATE",
        ["locality", "political"],
    ),
    (
        "PO Box 145, Elmira — no civic address",
        [["locality", "political"], ["administrative_area_level_3"]],
        "APPROXIMATE",
        ["locality", "political"],
    ),
    (
        "RR 2, Wallenstein — rural route, no civic address",
        [["locality", "political"], ["postal_code"]],
        "APPROXIMATE",
        ["locality", "political"],
    ),
]


class TestGeocodePrecision:
    @pytest.mark.parametrize(
        ("component_types", "location_type", "types"),
        [case[1:] for case in PRECISE_CASES],
        ids=[case[0] for case in PRECISE_CASES],
    )
    def test_real_addresses_are_precise(
        self,
        component_types: list[list[str]],
        location_type: str,
        types: list[str],
    ) -> None:
        assert is_precise_geocode_result(
            _result(
                component_types=component_types,
                location_type=location_type,
                types=types,
            )
        )

    @pytest.mark.parametrize(
        ("component_types", "location_type", "types"),
        [case[1:] for case in IMPRECISE_CASES],
        ids=[case[0] for case in IMPRECISE_CASES],
    )
    def test_fallback_matches_are_imprecise(
        self,
        component_types: list[list[str]],
        location_type: str,
        types: list[str],
    ) -> None:
        assert not is_precise_geocode_result(
            _result(
                component_types=component_types,
                location_type=location_type,
                types=types,
            )
        )

    def test_street_number_alone_is_not_enough(self) -> None:
        """A street_number on an APPROXIMATE match is still not a house."""
        assert not is_precise_geocode_result(
            _result(
                component_types=[["street_number"], ["route"], ["locality"]],
                location_type="APPROXIMATE",
            )
        )

    def test_precise_location_type_alone_is_not_enough(self) -> None:
        """A rooftop match on a building with no civic number is still not a house."""
        assert not is_precise_geocode_result(
            _result(
                component_types=[["premise"], ["route"], ["locality"]],
                location_type="ROOFTOP",
            )
        )

    def test_missing_address_components_key_raises(self) -> None:
        """A response shape we don't understand is a bug, not a silent False."""
        with pytest.raises(KeyError):
            is_precise_geocode_result(
                {"geometry": {"location_type": "ROOFTOP"}, "formatted_address": "x"}
            )

"""Tests for geocode precision detection.

The response fragments below are trimmed from real Google Geocoding API
responses for Waterloo Region addresses, so the predicate is exercised against
the shapes the API actually returns rather than invented ones.
"""

from __future__ import annotations

import logging
from typing import Any

import pytest

from app.utilities import google_maps_client
from app.utilities.google_maps_client import (
    GoogleMapsClient,
    is_precise_geocode_result,
)


def _result(
    *,
    component_types: list[list[str]],
    location_type: str,
    types: list[str] | None = None,
    partial_match: bool | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "address_components": [{"types": t} for t in component_types],
        "geometry": {"location_type": location_type, "location": {"lat": 0, "lng": 0}},
        "types": types or [],
        "formatted_address": "irrelevant",
        "place_id": "irrelevant",
    }
    # Google omits the key entirely on an exact match rather than sending false.
    if partial_match is not None:
        result["partial_match"] = partial_match
    return result


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

# Results that pass every structural check — street_number present, precise
# location_type — but that Google itself flagged as a guess. Without reading
# partial_match these are indistinguishable from an exact hit, and they are
# the dangerous shape: a real house, just not the one the admin typed.
PARTIAL_MATCH_CASES = [
    (
        "12 Maple Stret, Kitchener — misspelled street, matched Maple St",
        [["street_number"], ["route"], ["locality"], ["postal_code"]],
        "RANGE_INTERPOLATED",
        ["street_address"],
    ),
    (
        "45 Queen St, Waterloo — Queen St S in Kitchener won the match",
        [["street_number"], ["route"], ["locality"], ["postal_code"]],
        "ROOFTOP",
        ["street_address"],
    ),
    (
        "88 Main St — no city, matched a Main St in another town",
        [["street_number"], ["route"], ["locality"]],
        "ROOFTOP",
        ["street_address"],
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

    @pytest.mark.parametrize(
        ("component_types", "location_type", "types"),
        [case[1:] for case in PARTIAL_MATCH_CASES],
        ids=[case[0] for case in PARTIAL_MATCH_CASES],
    )
    def test_partial_matches_are_imprecise(
        self,
        component_types: list[list[str]],
        location_type: str,
        types: list[str],
    ) -> None:
        """Google's own "not an exact match" flag is disqualifying on its own."""
        assert not is_precise_geocode_result(
            _result(
                component_types=component_types,
                location_type=location_type,
                types=types,
                partial_match=True,
            )
        )

    @pytest.mark.parametrize(
        ("component_types", "location_type", "types"),
        [case[1:] for case in PARTIAL_MATCH_CASES],
        ids=[case[0] for case in PARTIAL_MATCH_CASES],
    )
    def test_same_results_are_precise_without_the_flag(
        self,
        component_types: list[list[str]],
        location_type: str,
        types: list[str],
    ) -> None:
        """The flag is doing the work — these shapes otherwise pass."""
        assert is_precise_geocode_result(
            _result(
                component_types=component_types,
                location_type=location_type,
                types=types,
            )
        )

    def test_explicit_false_partial_match_is_precise(self) -> None:
        """partial_match: false is an exact match, not a rejection."""
        assert is_precise_geocode_result(
            _result(
                component_types=[["street_number"], ["route"], ["locality"]],
                location_type="ROOFTOP",
                partial_match=False,
            )
        )

    def test_partial_match_on_an_already_imprecise_result_stays_imprecise(self) -> None:
        assert not is_precise_geocode_result(
            _result(
                component_types=[["locality", "political"]],
                location_type="APPROXIMATE",
                partial_match=True,
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


class _StubGeocoder:
    """Stands in for googlemaps.Client so no test touches the live API."""

    def __init__(self, results: list[dict[str, Any]]) -> None:
        self.results = results
        self.calls: list[tuple[str, str | None]] = []

    def geocode(self, address: str, region: str | None = None) -> list[dict[str, Any]]:
        self.calls.append((address, region))
        return self.results


class TestGeocodeAddressCarriesPartialMatch:
    """The flag has to survive the trip from the API response to GeocodeResult.

    The predicate reading partial_match is useless if the client hands it a
    dict with the key stripped out, so this exercises the real seam.
    """

    @staticmethod
    def _client(
        monkeypatch: pytest.MonkeyPatch, results: list[dict[str, Any]]
    ) -> GoogleMapsClient:
        monkeypatch.setattr(
            google_maps_client.googlemaps,
            "Client",
            lambda **_kwargs: _StubGeocoder(results),
        )
        return GoogleMapsClient(logging.getLogger("test"), "fake-key")

    def test_partial_match_response_is_not_precise(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        client = self._client(
            monkeypatch,
            [
                _result(
                    component_types=[["street_number"], ["route"], ["locality"]],
                    location_type="ROOFTOP",
                    types=["street_address"],
                    partial_match=True,
                )
            ],
        )

        result = client._geocode_address_sync("12 Maple Stret, Kitchener")

        assert result is not None
        assert result.is_precise is False
        assert client.client.calls == [("12 Maple Stret Kitchener", "ca")]

    def test_exact_response_is_precise(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = self._client(
            monkeypatch,
            [
                _result(
                    component_types=[["street_number"], ["route"], ["locality"]],
                    location_type="ROOFTOP",
                    types=["street_address"],
                )
            ],
        )

        result = client._geocode_address_sync("12 Maple St, Kitchener")

        assert result is not None
        assert result.is_precise is True

    def test_no_results_is_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = self._client(monkeypatch, [])

        assert client._geocode_address_sync("Nowhere At All") is None

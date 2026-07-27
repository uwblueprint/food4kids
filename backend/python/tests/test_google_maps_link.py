from urllib.parse import quote

import pytest

from app.utilities.google_maps_link import (
    MapWaypoint,
    build_google_maps_directions_url,
)


def _stop(
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> MapWaypoint:
    return MapWaypoint(address=address, latitude=latitude, longitude=longitude)


class TestBuildGoogleMapsDirectionsUrl:
    def test_origin_is_warehouse_coords(self) -> None:
        url = build_google_maps_directions_url(
            [_stop(address="1 Main St")], warehouse_lat=43.65, warehouse_lon=-79.38
        )
        assert url.startswith("https://www.google.com/maps/dir/43.65,-79.38/")

    def test_address_is_url_encoded(self) -> None:
        url = build_google_maps_directions_url(
            [_stop(address="10 Main St, Apt #2")], 43.0, -79.0
        )
        assert quote("10 Main St, Apt #2", safe="") in url
        assert " " not in url

    def test_falls_back_to_coords_when_no_address(self) -> None:
        url = build_google_maps_directions_url(
            [_stop(latitude=44.5, longitude=-79.5)], 43.0, -79.0
        )
        assert url.endswith("/44.5,-79.5")

    def test_prefers_address_over_coords(self) -> None:
        url = build_google_maps_directions_url(
            [_stop(address="7 Elm St", latitude=44.5, longitude=-79.5)], 43.0, -79.0
        )
        assert quote("7 Elm St", safe="") in url
        assert "44.5,-79.5" not in url.split("/dir/")[1]

    def test_preserves_stop_order(self) -> None:
        url = build_google_maps_directions_url(
            [_stop(address="first"), _stop(address="second"), _stop(address="third")],
            43.0,
            -79.0,
        )
        assert url == ("https://www.google.com/maps/dir/43.0,-79.0/first/second/third")

    def test_stop_with_neither_address_nor_coords_raises(self) -> None:
        with pytest.raises(ValueError, match="Stop 2 has neither"):
            build_google_maps_directions_url(
                [_stop(address="ok"), _stop()], 43.0, -79.0
            )

    def test_missing_only_one_coord_is_not_valid_coords(self) -> None:
        # latitude present but longitude None -> can't form "lat,lon".
        with pytest.raises(ValueError, match="Stop 1 has neither"):
            build_google_maps_directions_url([_stop(latitude=44.0)], 43.0, -79.0)

    def test_exactly_50_stops_ok(self) -> None:
        stops = [_stop(latitude=1.0, longitude=2.0) for _ in range(50)]
        url = build_google_maps_directions_url(stops, 43.0, -79.0)
        assert url.count("/1.0,2.0") == 50

    def test_more_than_50_stops_raises(self) -> None:
        stops = [_stop(latitude=1.0, longitude=2.0) for _ in range(51)]
        with pytest.raises(ValueError, match="maximum of 50 waypoints"):
            build_google_maps_directions_url(stops, 43.0, -79.0)

    def test_url_length_limit_raises(self) -> None:
        # A single very long address blows past the 2000-char browser limit.
        stops = [_stop(address="A" * 2100)]
        with pytest.raises(ValueError, match="exceeds the browser limit"):
            build_google_maps_directions_url(stops, 43.0, -79.0)

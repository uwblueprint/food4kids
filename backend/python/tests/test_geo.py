import pytest

from app.utilities.geo import haversine_km


@pytest.mark.parametrize(
    ("a", "b", "km"),
    [
        ((0.0, 0.0), (0.0, 0.0), 0.0),
        ((0.0, 0.0), (1.0, 0.0), 111.195),  # one degree of latitude
        ((0.0, 0.0), (0.0, 1.0), 111.195),  # one degree of longitude at the equator
        ((60.0, 0.0), (60.0, 1.0), 55.597),  # half as far at 60 degrees north
        ((0.0, 0.0), (0.0, 180.0), 20015.087),  # half the equator
        ((43.402343, -80.464610), (43.6532, -79.3832), 91.5),  # Kitchener-Toronto
    ],
)
def test_known_distances(
    a: tuple[float, float], b: tuple[float, float], km: float
) -> None:
    assert haversine_km(*a, *b) == pytest.approx(km, abs=0.1)
    assert haversine_km(*b, *a) == pytest.approx(km, abs=0.1)

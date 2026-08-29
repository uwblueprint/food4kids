"""The configured per-car capacity reaches the routing algorithm intact.

`SystemSettings.boxes_per_car` (and its two companions, `children_per_box` and
`dropoff_minutes`) are the only place those numbers are written down. Nothing
downstream may substitute one of its own: `RouteGenerationSettings` declares
them required, so a request that drops a key is a 422 rather than a plan built
against a number nobody configured.

These tests walk the whole path — settings row, the GET the configure screen
reads, POST /jobs/generate, the runner, the algorithm — and assert the numbers
that come out the far end are the ones that went in.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

import pytest
from sqlmodel import select

from app.models.enum import ProgressEnum
from app.models.job import Job
from app.models.location import Location
from app.models.location_group import LocationGroup
from app.models.system_settings import (
    DEFAULT_BOXES_PER_CAR,
    DEFAULT_CHILDREN_PER_BOX,
    DEFAULT_DROPOFF_MINUTES,
    SystemSettings,
)
from app.schemas.route_generation import RouteGenerationSettings
from app.services.implementations import route_generation_runner as runner
from app.services.implementations.mock_routing_algorithm import MockRoutingAlgorithm
from app.services.implementations.route_generation_runner import run_generation_job

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

WAREHOUSE_LAT = 43.4516
WAREHOUSE_LON = -80.4925
DRIVE_DATE = "2026-06-01T08:00:00"

# Deliberately none of the model defaults, so a fallback anywhere in the chain
# shows up as a wrong number rather than a coincidentally right one.
CONFIGURED_BOXES_PER_CAR = 7
CONFIGURED_CHILDREN_PER_BOX = 3
CONFIGURED_DROPOFF_MINUTES = 4

REQUIRED_SETTINGS_KEYS = (
    "max_boxes_per_driver",
    "children_per_box",
    "service_time_minutes",
)


class _CapturingAlgorithm:
    """Records the settings it was handed and returns one route."""

    def __init__(self) -> None:
        self.settings: RouteGenerationSettings | None = None

    async def generate_routes(
        self,
        locations: list[Location],
        warehouse_lat: float,  # noqa: ARG002
        warehouse_lon: float,  # noqa: ARG002
        settings: RouteGenerationSettings,
        timeout_seconds: float | None = None,  # noqa: ARG002
    ) -> list[list[Location]]:
        self.settings = settings
        return [locations]


@pytest.fixture(autouse=True)
def fake_polyline(monkeypatch: pytest.MonkeyPatch) -> None:
    """No test in this file may reach the real Google Maps API."""

    async def _fetch(**_kwargs: Any) -> tuple[str, float]:
        return "fake-polyline", 12.5

    monkeypatch.setattr(runner, "fetch_route_polyline", _fetch)


async def _configure_settings(client: AsyncClient) -> dict[str, Any]:
    """Set the org's capacity the way an admin would, and read it back the way
    the configure screen does."""
    patched = await client.patch(
        "/system-settings/",
        json={
            "boxes_per_car": CONFIGURED_BOXES_PER_CAR,
            "children_per_box": CONFIGURED_CHILDREN_PER_BOX,
            "dropoff_minutes": CONFIGURED_DROPOFF_MINUTES,
            "warehouse_latitude": WAREHOUSE_LAT,
            "warehouse_longitude": WAREHOUSE_LON,
        },
    )
    assert patched.status_code == 200

    response = await client.get("/system-settings/")
    assert response.status_code == 200
    return dict(response.json())


def _settings_body(settings: dict[str, Any]) -> dict[str, Any]:
    """The request body the configure screen builds from a settings row."""
    return {
        "route_start_time": DRIVE_DATE,
        "num_routes": 1,
        "return_to_warehouse": False,
        "max_boxes_per_driver": settings["boxes_per_car"],
        "children_per_box": settings["children_per_box"],
        "service_time_minutes": settings["dropoff_minutes"],
    }


async def _seed_group(session: AsyncSession) -> LocationGroup:
    group = LocationGroup(name="Monday Group", color="#FF5733")
    session.add(group)
    await session.commit()
    await session.refresh(group)

    for index in range(3):
        session.add(
            Location(
                location_group_id=group.location_group_id,
                name=f"Family {index}",
                contact_name=f"Family {index}",
                address=f"{index} King St, Kitchener, ON",
                phone_primary="tel:+1-519-576-0000",
                delivery_type="Family",
                latitude=43.46 + index * 0.01,
                longitude=-80.49,
                num_children=2,
            )
        )
    await session.commit()
    return group


async def _claim_job(session: AsyncSession, job_id: UUID) -> None:
    """Move a queued job to RUNNING, as the worker does before running it."""
    job = (
        (await session.execute(select(Job).where(Job.job_id == job_id))).scalars().one()
    )
    job.progress = ProgressEnum.RUNNING
    session.add(job)
    await session.commit()


@pytest.mark.asyncio
async def test_configured_capacity_reaches_the_algorithm(
    async_client: AsyncClient, test_session: AsyncSession
) -> None:
    """Settings row -> GET -> POST /jobs/generate -> runner -> algorithm.

    The point of this test: the numbers the algorithm plans against are the
    ones on the settings row, not a default from any layer in between.
    """
    settings = await _configure_settings(async_client)
    assert settings["boxes_per_car"] == CONFIGURED_BOXES_PER_CAR

    group = await _seed_group(test_session)

    response = await async_client.post(
        "/jobs/generate",
        json={
            "location_group": {
                "location_group_id": str(group.location_group_id),
                "name": group.name,
                "color": group.color,
            },
            "settings": _settings_body(settings),
        },
    )
    assert response.status_code == 202
    job_id = UUID(response.json()["job_id"])

    await _claim_job(test_session, job_id)
    algorithm = _CapturingAlgorithm()
    await run_generation_job(job_id, test_session, algorithm)

    assert algorithm.settings is not None
    assert algorithm.settings.max_boxes_per_driver == CONFIGURED_BOXES_PER_CAR
    assert algorithm.settings.children_per_box == CONFIGURED_CHILDREN_PER_BOX
    assert algorithm.settings.service_time_minutes == CONFIGURED_DROPOFF_MINUTES


@pytest.mark.asyncio
@pytest.mark.parametrize("omitted", REQUIRED_SETTINGS_KEYS)
async def test_omitting_a_configured_number_is_rejected(
    async_client: AsyncClient, omitted: str
) -> None:
    """A dropped key is a 422, never a silent substitution.

    This is the failure the required fields exist to prevent: the configure
    screen posting before settings resolved, so the key falls out of the JSON.
    """
    body = _settings_body(
        {
            "boxes_per_car": CONFIGURED_BOXES_PER_CAR,
            "children_per_box": CONFIGURED_CHILDREN_PER_BOX,
            "dropoff_minutes": CONFIGURED_DROPOFF_MINUTES,
        }
    )
    del body[omitted]

    response = await async_client.post(
        "/jobs/generate",
        json={
            "location_group": {"name": "Monday Group", "color": "#FF5733"},
            "settings": body,
        },
    )

    assert response.status_code == 422
    assert omitted in response.text


@pytest.mark.asyncio
async def test_all_configured_numbers_present_is_accepted(
    async_client: AsyncClient,
) -> None:
    """The 422s above are about the missing key, not a broken happy path."""
    response = await async_client.post(
        "/jobs/generate",
        json={
            "location_group": {"name": "Monday Group", "color": "#FF5733"},
            "settings": _settings_body(
                {
                    "boxes_per_car": CONFIGURED_BOXES_PER_CAR,
                    "children_per_box": CONFIGURED_CHILDREN_PER_BOX,
                    "dropoff_minutes": CONFIGURED_DROPOFF_MINUTES,
                }
            ),
        },
    )
    assert response.status_code == 202


@pytest.mark.parametrize("field", REQUIRED_SETTINGS_KEYS)
def test_route_generation_settings_declare_no_default(field: str) -> None:
    """Guard against a default creeping back in.

    A default here outranks the configured value whenever a caller omits the
    key, which is exactly how a capacity of 14 once replaced a configured 10.
    """
    assert RouteGenerationSettings.model_fields[field].is_required()


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("max_boxes_per_driver", 0),
        ("children_per_box", 0),
    ],
)
def test_unusable_configured_numbers_are_rejected(field: str, expected: int) -> None:
    """A capacity or divisor of zero can't size a route."""
    values: dict[str, Any] = {
        "route_start_time": datetime(2026, 6, 1, 8, 0),
        "num_routes": 1,
        "max_boxes_per_driver": CONFIGURED_BOXES_PER_CAR,
        "children_per_box": CONFIGURED_CHILDREN_PER_BOX,
        "service_time_minutes": CONFIGURED_DROPOFF_MINUTES,
        field: expected,
    }
    with pytest.raises(ValueError, match=field):
        RouteGenerationSettings(**values)


def test_settings_defaults_are_the_single_source() -> None:
    """The literal defaults live here and only here.

    Changing what a new F4K install starts with is a one-line edit in
    ``app.models.system_settings``; this test is what pins those values, so a
    default reappearing in a schema or algorithm module is a failure above,
    not a second copy of the number that quietly drifts.
    """
    assert DEFAULT_BOXES_PER_CAR == 10
    assert DEFAULT_CHILDREN_PER_BOX == 2
    assert DEFAULT_DROPOFF_MINUTES == 3

    fresh = SystemSettings()
    assert fresh.boxes_per_car == DEFAULT_BOXES_PER_CAR
    assert fresh.children_per_box == DEFAULT_CHILDREN_PER_BOX
    assert fresh.dropoff_minutes == DEFAULT_DROPOFF_MINUTES


@pytest.mark.asyncio
async def test_routing_algorithm_hands_the_capacity_to_clustering() -> None:
    """The routing -> clustering hand-off carries the cap.

    A routing algorithm that clusters must pass the configured capacity down;
    clustering has no default of its own to fall back on.
    """
    captured: dict[str, Any] = {}

    class _SpyClustering:
        def __init__(self, children_per_box: int) -> None:
            captured["children_per_box"] = children_per_box

        async def cluster_locations(
            self,
            locations: list[Location],
            num_clusters: int,
            max_boxes_per_cluster: int,
            timeout_seconds: float | None = None,  # noqa: ARG002
        ) -> list[list[Location]]:
            captured["max_boxes_per_cluster"] = max_boxes_per_cluster
            captured["num_clusters"] = num_clusters
            return [locations]

    import app.services.implementations.mock_routing_algorithm as mock_module

    original = mock_module.MockClusteringAlgorithm
    mock_module.MockClusteringAlgorithm = _SpyClustering  # type: ignore[misc,assignment]
    try:
        await MockRoutingAlgorithm().generate_routes(
            [],
            WAREHOUSE_LAT,
            WAREHOUSE_LON,
            RouteGenerationSettings(
                route_start_time=datetime(2026, 6, 1, 8, 0),
                num_routes=2,
                max_boxes_per_driver=CONFIGURED_BOXES_PER_CAR,
                children_per_box=CONFIGURED_CHILDREN_PER_BOX,
                service_time_minutes=CONFIGURED_DROPOFF_MINUTES,
            ),
        )
    finally:
        mock_module.MockClusteringAlgorithm = original  # type: ignore[misc]

    assert captured["max_boxes_per_cluster"] == CONFIGURED_BOXES_PER_CAR
    assert captured["children_per_box"] == CONFIGURED_CHILDREN_PER_BOX
    assert captured["num_clusters"] == 2

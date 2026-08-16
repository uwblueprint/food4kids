"""The auth split on ``/system-settings``: ``/contact`` is public, the rest is not.

``conftest.py``'s client fixtures stub ``require_admin`` to a no-op, which would
make a gated route indistinguishable from a public one — so these tests build
their own app with only the session overridden, and send no token.
"""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import create_app
from app.dependencies.services import get_gcp_storage_client
from app.models import get_session
from app.models.system_settings import SystemSettings, SystemSettingsUpdate


@pytest_asyncio.fixture
async def anonymous_client(
    test_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """A client whose app has *no* auth overrides — requests arrive tokenless."""
    app = create_app()

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield test_session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_gcp_storage_client] = lambda: None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def settings_row(test_session: AsyncSession) -> Any:
    """The singleton settings row, as app startup guarantees it."""
    settings = SystemSettings()
    test_session.add(settings)
    await test_session.commit()
    await test_session.refresh(settings)
    return settings


async def _set_contact(
    session: AsyncSession, settings: SystemSettings, **fields: Any
) -> None:
    """Write contact fields the way a PATCH would.

    A ``table=True`` SQLModel skips validation on assignment, so the value goes
    through ``SystemSettingsUpdate`` to get the RFC 3966 normalization
    production applies.
    """
    validated = SystemSettingsUpdate(**fields)
    for key in fields:
        setattr(settings, key, getattr(validated, key))
    session.add(settings)
    await session.commit()
    await session.refresh(settings)


# ---------------------------------------------------------------------------
# The public half
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_contact_readable_without_a_token(
    anonymous_client: AsyncClient, test_session: AsyncSession, settings_row: Any
) -> None:
    """The whole point: a tokenless caller gets the contact details."""
    await _set_contact(
        test_session,
        settings_row,
        contact_name="Emily Loro",
        contact_phone="519-576-3443 ext 1",
    )

    response = await anonymous_client.get("/system-settings/contact")

    assert response.status_code == 200
    assert response.json() == {
        "contact_name": "Emily Loro",
        # Stored RFC 3966, so the frontend can use it as an href untouched.
        "contact_phone": "tel:+1-519-576-3443;ext=1",
    }


@pytest.mark.asyncio
async def test_contact_exposes_only_name_and_phone(
    anonymous_client: AsyncClient, test_session: AsyncSession, settings_row: Any
) -> None:
    """The guard that matters: warehouse coords and column maps live on the
    same row, and none of it may reach an unauthenticated caller."""
    settings_row.warehouse_location = "50 Sportsworld Crossing Rd, Kitchener"
    settings_row.warehouse_latitude = 43.4123
    settings_row.warehouse_longitude = -80.4567
    settings_row.import_column_map = {"Name": "name", "Phone": "phone_primary"}
    settings_row.f4k_wr_email = "info@food4kidswr.ca"
    await _set_contact(test_session, settings_row, contact_name="Emily Loro")

    response = await anonymous_client.get("/system-settings/contact")

    assert response.status_code == 200
    assert set(response.json()) == {"contact_name", "contact_phone"}


@pytest.mark.asyncio
@pytest.mark.usefixtures("settings_row")
async def test_contact_returns_nulls_when_unconfigured(
    anonymous_client: AsyncClient,
) -> None:
    """Null rather than 404, so the frontend renders its no-number fallback."""
    response = await anonymous_client.get("/system-settings/contact")

    assert response.status_code == 200
    assert response.json() == {"contact_name": None, "contact_phone": None}


@pytest.mark.asyncio
async def test_contact_returns_name_without_phone(
    anonymous_client: AsyncClient, test_session: AsyncSession, settings_row: Any
) -> None:
    """The two fields are independent; one set and one not must not blank both."""
    await _set_contact(test_session, settings_row, contact_name="Emily Loro")

    response = await anonymous_client.get("/system-settings/contact")

    assert response.json() == {"contact_name": "Emily Loro", "contact_phone": None}


@pytest.mark.asyncio
async def test_contact_returns_phone_without_name(
    anonymous_client: AsyncClient, test_session: AsyncSession, settings_row: Any
) -> None:
    """...and the mirror case."""
    await _set_contact(test_session, settings_row, contact_phone="(519) 576-3443")

    response = await anonymous_client.get("/system-settings/contact")

    assert response.json() == {
        "contact_name": None,
        "contact_phone": "tel:+1-519-576-3443",
    }


@pytest.mark.asyncio
async def test_contact_missing_settings_row_is_a_server_error(
    anonymous_client: AsyncClient,
) -> None:
    """No ``settings_row`` fixture, so the startup invariant is broken.

    ``require_settings`` raises rather than inventing an empty contact, so this
    500s instead of claiming with a 200 that there is no phone number.
    """
    response = await anonymous_client.get("/system-settings/contact")

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# The admin half stays shut
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.usefixtures("settings_row")
async def test_full_settings_still_requires_a_token(
    anonymous_client: AsyncClient,
) -> None:
    """Same router, same tokenless client, refused — without this the tests
    above would also pass if the router had simply lost its auth."""
    response = await anonymous_client.get("/system-settings/")

    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.usefixtures("settings_row")
async def test_patch_still_requires_a_token(anonymous_client: AsyncClient) -> None:
    """The write path is untouched by the carve-out."""
    response = await anonymous_client.patch(
        "/system-settings/", json={"contact_phone": "519-576-3443"}
    )

    assert response.status_code == 401

"""The auth split on ``/system-settings``.

``GET /system-settings/contact`` is the one route on this router that any
caller may read, because its consumers cannot present an admin token: the
driver route screen's "Call Food4Kids" button, and the catch-all error page,
which renders for logged-out visitors. Everything else on the settings row —
warehouse coordinates, email-reminder schedule, import column maps — stays
behind ``require_admin``.

The shared client fixtures in ``conftest.py`` override ``require_admin`` to a
no-op, which would make an admin-only route look public and a public route look
indistinguishable from it. So these tests build their own app with *only* the
session overridden, and send no ``Authorization`` header at all.
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

    A ``table=True`` SQLModel skips validation on assignment, so setting
    ``contact_phone`` directly would store whatever string the test typed.
    Routing the value through ``SystemSettingsUpdate`` runs the same
    ``validate_contact_phone`` the endpoint does, so the stored form under test
    is the RFC 3966 one production actually holds.
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
    """No other settings field rides along, however the row is populated.

    This is the guard that matters: the row carries warehouse coordinates and
    import column maps, and none of it may reach an unauthenticated caller.
    """
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
    """A fresh settings row has neither field set; both come back null rather
    than 404, so the frontend renders its no-number fallback."""
    response = await anonymous_client.get("/system-settings/contact")

    assert response.status_code == 200
    assert response.json() == {"contact_name": None, "contact_phone": None}


@pytest.mark.asyncio
async def test_contact_returns_name_without_phone(
    anonymous_client: AsyncClient, test_session: AsyncSession, settings_row: Any
) -> None:
    """The two fields are independent — a configured name with no number is a
    reachable state, and the endpoint reports it rather than blanking both."""
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
    """No ``settings_row`` fixture here, so the startup invariant is broken.

    ``require_settings`` raises rather than inventing an empty contact, per the
    fail-loudly rule — a missing row is a broken deployment, not a state to
    paper over. ``UnhandledExceptionMiddleware`` turns that into a 500, so the
    frontend sees a failed request and falls back, rather than being told with
    a 200 that Food4Kids has no phone number.
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
    """Same router, same tokenless client: the full row is refused.

    Without this the contact test above proves nothing — it could be passing
    because the router lost its auth, not because one route was carved out.
    """
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

"""
Comprehensive integration tests for API routes.

Tests cover:
- Driver routes (CRUD operations)
- Location routes (CRUD operations)
- Route routes (read and delete operations)
- Route group routes (CRUD operations)
- Error handling (404s, validation errors)
"""

import json
from datetime import date, datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import DriverAccess, require_self_driver_or_admin
from app.dependencies.services import get_google_maps_client
from app.models.enum import ProgressEnum
from app.models.location import Location
from app.models.location_group import LocationGroup
from app.models.note_chain import NoteChain
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_snapshot import RouteSnapshot
from app.models.route_stop import RouteStop
from app.models.route_stop_snapshot import RouteStopSnapshot
from app.utilities.google_maps_client import GeocodeResult

IMPORT_COLUMN_MAP = {
    "contact_name": "Name",
    "address": "Address",
    "delivery_group": "Delivery Group",
    "phone_primary": "Phone",
    "phone_secondary": "Secondary Phone",
    "num_children": "Children",
}


class FakeGoogleMapsClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def geocode_address(self, address: str) -> GeocodeResult | None:
        self.calls.append(address)
        if "Invalid" in address:
            return None
        formatted_address = (
            address if address.startswith("Formatted ") else f"Formatted {address}"
        )
        return GeocodeResult(
            formatted_address=formatted_address,
            place_id=f"place-{address}",
            latitude=43.0,
            longitude=-80.0,
        )


def import_review_request(rows: list[dict[str, str]]) -> dict[str, Any]:
    headers = [
        "Name",
        "Address",
        "Delivery Group",
        "Phone",
        "Secondary Phone",
        "Children",
    ]
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(row.get(header, "") for header in headers))
    return {
        "data": {"column_map": json.dumps(IMPORT_COLUMN_MAP)},
        "files": {"file": ("locations.csv", "\n".join(lines).encode(), "text/csv")},
    }


class TestDriverRoutes:
    """Test suite for driver API routes."""

    @pytest.mark.asyncio
    async def test_get_drivers_empty(self, async_client: AsyncClient) -> None:
        """Test GET /drivers returns empty list when no drivers exist."""
        response = await async_client.get("/drivers/")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_initialize_driver(
        self,
        async_client: AsyncClient,
        sample_driver_data: dict[str, Any],
    ) -> None:
        """Test POST /drivers creates a new driver."""

        # We don't want to actually to send an email so we mock the call
        with (
            patch(
                "app.services.implementations.auth_service.AuthService.send_create_password_email"
            ),
            patch(
                "app.dependencies.auth.auth_service.is_authorized_by_role",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):
            driver_register_data = {
                "first_name": sample_driver_data["first_name"],
                "last_name": sample_driver_data["last_name"],
                "email": "newdriver@example.com",
                "phone": sample_driver_data["phone"],
                "address": sample_driver_data["address"],
                "license_plate": sample_driver_data["license_plate"],
                "car_make_model": sample_driver_data["car_make_model"],
            }
            response = await async_client.post(
                "/drivers/initialize",
                json=driver_register_data,
                headers={"Authorization": "Bearer test-token"},
            )
            assert response.status_code == 201
            data = response.json()
            assert data["phone"] == sample_driver_data["phone"]
            assert data["license_plate"] == sample_driver_data["license_plate"]
            assert data["role"] == "driver"
            assert data["email"] == "newdriver@example.com"
            assert data["auth_id"] is None
            assert "driver_id" in data

    @pytest.mark.asyncio
    async def test_register_driver(
        self,
        async_client: AsyncClient,
        sample_driver_data: dict[str, Any],
    ) -> None:
        """Test POST /drivers/register creates a new driver."""
        mock_firebase_user = MagicMock()
        mock_firebase_user.uid = "fake-auth-id-123"

        from app.models.driver import Driver
        from app.models.user import User
        from app.models.user_invite import UserInvite

        fake_user = User(
            user_id=uuid4(),
            auth_id=None,
            email="testemail@gmail.com",
            first_name="Test",
            last_name="User",
            role="driver",
        )

        fake_driver = Driver(
            user_id=fake_user.user_id,
            phone=sample_driver_data["phone"],
            address=sample_driver_data["address"],
            license_plate=sample_driver_data["license_plate"],
            car_make_model=sample_driver_data["car_make_model"],
        )
        fake_user.driver = fake_driver

        fake_user_invite = UserInvite(
            user_invite_id=uuid4(),
            user_id=fake_user.user_id,
            is_used=False,
            expires_at=datetime.now(timezone.utc) + timedelta(days=2),
        )
        fake_user_invite.user = fake_user

        fake_auth_dto = {
            "access_token": "fake-access-token",
            "first_name": sample_driver_data["first_name"],
            "last_name": sample_driver_data["last_name"],
            "id": str(uuid4()),
            "email": "newdriver@example.com",
            "role": "driver",
        }
        # We don't want to actually call firebase so we mock the call
        with (
            patch("firebase_admin.auth.create_user", return_value=mock_firebase_user),
            patch("firebase_admin.auth.set_custom_user_claims"),
            patch("firebase_admin.auth.delete_user"),
            patch(
                "sqlalchemy.ext.asyncio.AsyncSession.refresh", new_callable=AsyncMock
            ),
            patch("sqlalchemy.ext.asyncio.AsyncSession.commit", new_callable=AsyncMock),
            patch(
                "app.services.implementations.user_invite_service.UserInviteService.get_user_invite_by_id",
                return_value=fake_user_invite,
            ),
            patch(
                "app.services.implementations.auth_service.AuthService.generate_token",
                return_value=(fake_auth_dto, "fake_refresh_token"),
            ),
        ):
            user_finalize_data = {
                "user_invite_id": str(fake_user_invite.user_invite_id),
                "password": "testing123",
            }
            response = await async_client.post(
                "/drivers/register", json=user_finalize_data
            )
            assert response.status_code == 201
            data = response.json()
            assert data["driver"]["phone"] == sample_driver_data["phone"]
            assert (
                data["driver"]["license_plate"] == sample_driver_data["license_plate"]
            )
            assert data["driver"]["role"] == "driver"
            assert data["auth"]["email"] == "newdriver@example.com"
            assert "access_token" in data["auth"]
            assert "driver_id" in data["driver"]

    @pytest.mark.asyncio
    async def test_get_drivers_with_data(
        self, async_client: AsyncClient, test_driver: Any
    ) -> None:
        """Test GET /drivers returns list of drivers."""
        response = await async_client.get("/drivers/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert str(data[0]["driver_id"]) == str(test_driver.driver_id)

    @pytest.mark.asyncio
    async def test_get_driver_by_id(
        self, async_client: AsyncClient, test_driver: Any
    ) -> None:
        """Test GET /drivers/{driver_id} returns specific driver."""
        response = await async_client.get(f"/drivers/{test_driver.driver_id}")
        assert response.status_code == 200
        data = response.json()
        assert str(data["driver_id"]) == str(test_driver.driver_id)
        assert data["phone"] == test_driver.phone

    @pytest.mark.asyncio
    async def test_get_driver_not_found(self, async_client: AsyncClient) -> None:
        """Test GET /drivers/{driver_id} returns 404 for non-existent driver."""
        fake_id = uuid4()
        response = await async_client.get(f"/drivers/{fake_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_driver(
        self, async_client: AsyncClient, test_driver: Any
    ) -> None:
        """Test PUT /drivers/{driver_id} updates a driver."""
        update_data = {"address": "456 New Address St"}
        response = await async_client.put(
            f"/drivers/{test_driver.driver_id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == "456 New Address St"

    @pytest.mark.asyncio
    async def test_update_driver_clears_nullable_fields(
        self,
        async_client: AsyncClient,
        test_driver: Any,
        test_session: AsyncSession,
    ) -> None:
        """Test PUT /drivers/{driver_id} clears explicit null values."""
        test_driver.partner_driver_name = "Pat Partner"
        await test_session.commit()

        response = await async_client.put(
            f"/drivers/{test_driver.driver_id}",
            json={"partner_driver_name": None},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["partner_driver_name"] is None

    @pytest.mark.asyncio
    async def test_self_driver_updates_own_name_and_phone(
        self,
        client_with_overrides: Any,
        test_driver: Any,
        test_session: AsyncSession,
    ) -> None:
        """Self-driver update can edit only User name fields and Driver phone."""
        from app.models.user import User

        self_client = await client_with_overrides(
            {require_self_driver_or_admin: lambda: DriverAccess.SELF}
        )
        with (
            patch("firebase_admin.auth.update_user") as mock_update_user,
            patch("firebase_admin.auth.set_custom_user_claims") as mock_claims,
        ):
            response = await self_client.put(
                f"/drivers/{test_driver.driver_id}",
                json={
                    "first_name": "Updated",
                    "last_name": "Driver",
                    "phone": "+14165550123",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Driver"
        assert data["phone"] == "+14165550123"

        await test_session.refresh(test_driver)
        user = await test_session.get(User, test_driver.user_id)
        assert user is not None
        assert user.first_name == "Updated"
        assert user.last_name == "Driver"
        assert test_driver.phone == "+14165550123"
        mock_update_user.assert_called_once_with(
            user.auth_id,
            display_name="Updated Driver",
        )
        mock_claims.assert_called_once_with(
            user.auth_id,
            {
                "role": user.role,
                "given_name": "Updated",
                "family_name": "Driver",
            },
        )

    @pytest.mark.asyncio
    async def test_self_driver_cannot_update_admin_only_fields(
        self,
        client_with_overrides: Any,
        test_driver: Any,
        test_session: AsyncSession,
    ) -> None:
        """Self-driver update rejects admin-only fields and does not persist them."""
        original_phone = test_driver.phone
        original_address = test_driver.address
        original_active = test_driver.active
        self_client = await client_with_overrides(
            {require_self_driver_or_admin: lambda: DriverAccess.SELF}
        )

        response = await self_client.put(
            f"/drivers/{test_driver.driver_id}",
            json={
                "phone": "+14165550123",
                "address": "123 Admin Only St",
                "active": False,
            },
        )

        assert response.status_code == 403
        await test_session.refresh(test_driver)
        assert test_driver.phone == original_phone
        assert test_driver.address == original_address
        assert test_driver.active is original_active

    @pytest.mark.asyncio
    async def test_update_driver_rejects_explicit_null(
        self,
        async_client: AsyncClient,
        test_driver: Any,
        test_session: AsyncSession,
    ) -> None:
        """Explicit null for a non-nullable field is a 422, not a commit-time 500."""
        from app.models.user import User

        user = await test_session.get(User, test_driver.user_id)
        assert user is not None
        original_first_name = user.first_name

        response = await async_client.put(
            f"/drivers/{test_driver.driver_id}",
            json={"first_name": None},
        )

        assert response.status_code == 422
        await test_session.refresh(user)
        assert user.first_name == original_first_name

    @pytest.mark.asyncio
    async def test_admin_updates_driver_name_and_admin_only_fields(
        self,
        async_client: AsyncClient,
        test_driver: Any,
        test_session: AsyncSession,
    ) -> None:
        """Admin update keeps the full DriverUpdate surface, including User names."""
        from app.models.user import User

        with (
            patch("firebase_admin.auth.update_user") as mock_update_user,
            patch("firebase_admin.auth.set_custom_user_claims") as mock_claims,
        ):
            response = await async_client.put(
                f"/drivers/{test_driver.driver_id}",
                json={
                    "first_name": "Admin",
                    "last_name": "Updated",
                    "address": "456 Admin Address St",
                    "active": False,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Admin"
        assert data["last_name"] == "Updated"
        assert data["address"] == "456 Admin Address St"
        assert data["active"] is False

        await test_session.refresh(test_driver)
        user = await test_session.get(User, test_driver.user_id)
        assert user is not None
        assert user.first_name == "Admin"
        assert user.last_name == "Updated"
        assert test_driver.address == "456 Admin Address St"
        assert test_driver.active is False
        mock_update_user.assert_called_once_with(
            user.auth_id,
            display_name="Admin Updated",
        )
        mock_claims.assert_called_once_with(
            user.auth_id,
            {
                "role": user.role,
                "given_name": "Admin",
                "family_name": "Updated",
            },
        )

    @pytest.mark.asyncio
    async def test_update_driver_not_found(self, async_client: AsyncClient) -> None:
        """Test PUT /drivers/{driver_id} returns 404 for non-existent driver."""
        fake_id = uuid4()
        update_data = {"address": "456 New Address St"}
        response = await async_client.put(f"/drivers/{fake_id}", json=update_data)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_driver(
        self, async_client: AsyncClient, test_driver: Any
    ) -> None:
        """Test DELETE /drivers/{driver_id} deletes a driver."""
        response = await async_client.delete(f"/drivers/{test_driver.driver_id}")
        assert response.status_code == 204

        # Verify deletion
        get_response = await async_client.get(f"/drivers/{test_driver.driver_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_driver_by_email(
        self, async_client: AsyncClient, test_driver: Any, test_session: AsyncSession
    ) -> None:
        """Test GET /drivers?email= filters by email."""
        # Get the user associated with test_driver to find the email
        from sqlmodel import select

        from app.models.user import User

        result = await test_session.execute(
            select(User).where(User.user_id == test_driver.user_id)
        )
        user = result.scalar_one()

        response = await async_client.get(f"/drivers/?email={user.email}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert str(data[0]["driver_id"]) == str(test_driver.driver_id)


class TestLocationRoutes:
    """Test suite for location API routes."""

    @pytest.mark.asyncio
    async def test_get_locations_empty(self, async_client: AsyncClient) -> None:
        """Test GET /locations returns empty paginated response when no locations exist."""
        response = await async_client.get("/locations/")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["total_pages"] == 0

    @pytest.mark.asyncio
    async def test_create_location(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """Test POST /locations creates a new location."""
        payload = {
            **sample_location_data,
            "location_group_id": str(test_location_group.location_group_id),
        }
        response = await async_client.post("/locations/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["contact_name"] == sample_location_data["contact_name"]
        assert data["address"] == sample_location_data["address"]
        assert "location_id" in data
        assert data["note_chain_id"] is not None  # auto-created

    @pytest.mark.asyncio
    async def test_create_location_accepts_configured_delivery_type(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """POST /locations validates delivery_type against system settings."""
        settings_response = await async_client.patch(
            "/system-settings/",
            json={"delivery_types": ["School", "Family", "Pantry"]},
        )
        assert settings_response.status_code == 200

        response = await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "location_group_id": str(test_location_group.location_group_id),
                "delivery_type": "Pantry",
            },
        )

        assert response.status_code == 201
        assert response.json()["delivery_type"] == "Pantry"

    @pytest.mark.asyncio
    async def test_create_location_rejects_unknown_delivery_type(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """POST /locations fails fast when delivery_type is not configured."""
        response = await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "location_group_id": str(test_location_group.location_group_id),
                "delivery_type": "Unknown",
            },
        )

        assert response.status_code == 400
        assert "Unknown delivery_type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_locations_with_data(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """Test GET /locations returns paginated list of locations."""
        # Create a location first
        create_response = await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "location_group_id": str(test_location_group.location_group_id),
            },
        )
        assert create_response.status_code == 201

        # Get all locations
        response = await async_client.get("/locations/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_locations_filters_by_delivery_type(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """GET /locations filters school vs family locations by delivery_type."""
        school_response = await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "location_group_id": str(test_location_group.location_group_id),
                "name": "Central Elementary",
                "contact_name": "School Contact",
                "phone_primary": "(555) 111-1111",
                "delivery_type": "School",
            },
        )
        family_response = await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "location_group_id": str(test_location_group.location_group_id),
                "name": "Family Contact",
                "contact_name": "Family Contact",
                "phone_primary": "(555) 222-2222",
                "delivery_type": "Family",
            },
        )
        assert school_response.status_code == 201
        assert family_response.status_code == 201

        school_id = school_response.json()["location_id"]
        family_id = family_response.json()["location_id"]

        school_filter = await async_client.get(
            "/locations/", params={"delivery_type": "School"}
        )
        assert school_filter.status_code == 200
        school_ids = {loc["location_id"] for loc in school_filter.json()["items"]}
        assert school_id in school_ids
        assert family_id not in school_ids

        family_filter = await async_client.get(
            "/locations/", params={"delivery_type": "Family"}
        )
        assert family_filter.status_code == 200
        family_ids = {loc["location_id"] for loc in family_filter.json()["items"]}
        assert family_id in family_ids
        assert school_id not in family_ids

    @pytest.mark.asyncio
    async def test_get_locations_rejects_unknown_delivery_type_filter(
        self, async_client: AsyncClient
    ) -> None:
        """GET /locations validates delivery_type filters against settings."""
        response = await async_client.get(
            "/locations/", params={"delivery_type": "Unknown"}
        )

        assert response.status_code == 422
        assert "Unknown delivery_type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_locations_filters_by_location_group(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_location_group: Any,
    ) -> None:
        """GET /locations filters locations by a single location_group_id."""
        other_group = LocationGroup(name="Other Delivery Group", color="#3357FF")
        target_location = Location(
            location_group_id=test_location_group.location_group_id,
            name="Target Family",
            contact_name="Target Family",
            address="1 Target St",
            phone_primary="5551111111",
            delivery_type="Family",
            in_roster=True,
        )
        other_location = Location(
            location_group_id=other_group.location_group_id,
            name="Other Family",
            contact_name="Other Family",
            address="1 Other St",
            phone_primary="5552222222",
            delivery_type="Family",
            in_roster=True,
        )
        test_session.add(other_group)
        test_session.add_all([target_location, other_location])
        await test_session.commit()
        await test_session.refresh(target_location)
        await test_session.refresh(other_location)

        response = await async_client.get(
            "/locations/",
            params={"location_group_id": str(test_location_group.location_group_id)},
        )

        assert response.status_code == 200
        location_ids = {loc["location_id"] for loc in response.json()["items"]}
        assert str(target_location.location_id) in location_ids
        assert str(other_location.location_id) not in location_ids

    @pytest.mark.asyncio
    async def test_get_locations_filters_by_multiple_location_groups(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_location_group: Any,
    ) -> None:
        """GET /locations accepts repeated location_group_id query params."""
        second_group = LocationGroup(name="Second Delivery Group", color="#33FF57")
        third_group = LocationGroup(name="Third Delivery Group", color="#5733FF")
        first_location = Location(
            location_group_id=test_location_group.location_group_id,
            name="First Group Family",
            contact_name="First Group Family",
            address="1 First St",
            phone_primary="5551111111",
            delivery_type="Family",
            in_roster=True,
        )
        second_location = Location(
            location_group_id=second_group.location_group_id,
            name="Second Group Family",
            contact_name="Second Group Family",
            address="1 Second St",
            phone_primary="5552222222",
            delivery_type="Family",
            in_roster=True,
        )
        third_location = Location(
            location_group_id=third_group.location_group_id,
            name="Third Group Family",
            contact_name="Third Group Family",
            address="1 Third St",
            phone_primary="5553333333",
            delivery_type="Family",
            in_roster=True,
        )
        test_session.add_all([second_group, third_group])
        test_session.add_all([first_location, second_location, third_location])
        await test_session.commit()
        await test_session.refresh(first_location)
        await test_session.refresh(second_location)
        await test_session.refresh(third_location)

        response = await async_client.get(
            "/locations/",
            params=[
                ("location_group_id", str(test_location_group.location_group_id)),
                ("location_group_id", str(second_group.location_group_id)),
            ],
        )

        assert response.status_code == 200
        location_ids = {loc["location_id"] for loc in response.json()["items"]}
        assert str(first_location.location_id) in location_ids
        assert str(second_location.location_id) in location_ids
        assert str(third_location.location_id) not in location_ids

    @pytest.mark.asyncio
    async def test_get_locations_filters_by_status(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_location_group: Any,
    ) -> None:
        """GET /locations derives status from in_roster + future route usage."""
        scheduled_location = Location(
            location_group_id=test_location_group.location_group_id,
            name="Scheduled Family",
            contact_name="Scheduled Family",
            address="1 Scheduled St",
            phone_primary="5551111111",
            delivery_type="Family",
            in_roster=True,
        )
        unscheduled_location = Location(
            location_group_id=test_location_group.location_group_id,
            name="Unscheduled Family",
            contact_name="Unscheduled Family",
            address="2 Unscheduled St",
            phone_primary="5552222222",
            delivery_type="Family",
            in_roster=True,
        )
        inactive_location = Location(
            location_group_id=test_location_group.location_group_id,
            name="Inactive Family",
            contact_name="Inactive Family",
            address="3 Inactive St",
            phone_primary="5553333333",
            delivery_type="Family",
            in_roster=False,
        )
        archived_scheduled_location = Location(
            location_group_id=test_location_group.location_group_id,
            name="Archived Scheduled Family",
            contact_name="Archived Scheduled Family",
            address="4 Archived Scheduled St",
            phone_primary="5554444444",
            delivery_type="Family",
            in_roster=False,
        )
        # RouteGroup must exist before Routes (Route.route_group_id is a
        # mandatory FK).
        route_group = RouteGroup(
            name="Future Route Group", drive_date=datetime(2099, 1, 1)
        )
        test_session.add(route_group)
        test_session.add_all(
            [
                scheduled_location,
                unscheduled_location,
                inactive_location,
                archived_scheduled_location,
            ]
        )
        await test_session.commit()
        await test_session.refresh(route_group)
        await test_session.refresh(scheduled_location)
        await test_session.refresh(unscheduled_location)
        await test_session.refresh(inactive_location)
        await test_session.refresh(archived_scheduled_location)

        route = Route(
            name="Future Route", length=1.0, route_group_id=route_group.route_group_id
        )
        archived_route = Route(
            name="Future Archived Route",
            length=1.0,
            route_group_id=route_group.route_group_id,
        )
        test_session.add_all([route, archived_route])
        await test_session.commit()
        await test_session.refresh(route)
        await test_session.refresh(archived_route)

        test_session.add_all(
            [
                RouteStop(
                    route_id=route.route_id,
                    location_id=scheduled_location.location_id,
                    stop_number=1,
                ),
                RouteStop(
                    route_id=archived_route.route_id,
                    location_id=archived_scheduled_location.location_id,
                    stop_number=1,
                ),
            ]
        )
        await test_session.commit()

        active_response = await async_client.get(
            "/locations/", params={"status": "Active"}
        )
        unscheduled_response = await async_client.get(
            "/locations/", params={"status": "Unscheduled"}
        )
        inactive_response = await async_client.get(
            "/locations/", params={"status": "Inactive"}
        )

        assert active_response.status_code == 200
        assert unscheduled_response.status_code == 200
        assert inactive_response.status_code == 200

        active_ids = {loc["location_id"] for loc in active_response.json()["items"]}
        unscheduled_ids = {
            loc["location_id"] for loc in unscheduled_response.json()["items"]
        }
        inactive_ids = {loc["location_id"] for loc in inactive_response.json()["items"]}

        assert str(scheduled_location.location_id) in active_ids
        assert str(archived_scheduled_location.location_id) in active_ids
        assert str(unscheduled_location.location_id) not in active_ids
        assert str(inactive_location.location_id) not in active_ids

        assert str(unscheduled_location.location_id) in unscheduled_ids
        assert str(scheduled_location.location_id) not in unscheduled_ids
        assert str(archived_scheduled_location.location_id) not in unscheduled_ids
        assert str(inactive_location.location_id) not in unscheduled_ids

        assert str(inactive_location.location_id) in inactive_ids
        assert str(scheduled_location.location_id) not in inactive_ids
        assert str(archived_scheduled_location.location_id) not in inactive_ids
        assert str(unscheduled_location.location_id) not in inactive_ids

    @pytest.mark.asyncio
    async def test_get_locations_filters_by_delivery_type_and_status(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_location_group: Any,
    ) -> None:
        """GET /locations combines delivery type and status filters."""
        active_school_location = Location(
            location_group_id=test_location_group.location_group_id,
            name="Central Elementary",
            contact_name="Active School",
            address="1 School St",
            phone_primary="5555555555",
            delivery_type="School",
            in_roster=True,
        )
        active_family_location = Location(
            location_group_id=test_location_group.location_group_id,
            name="Active Family",
            contact_name="Active Family",
            address="1 Family St",
            phone_primary="5556666666",
            delivery_type="Family",
            in_roster=True,
        )
        unscheduled_school_location = Location(
            location_group_id=test_location_group.location_group_id,
            name="Unscheduled Elementary",
            contact_name="Unscheduled School",
            address="2 School St",
            phone_primary="5557777777",
            delivery_type="School",
            in_roster=True,
        )
        route_group = RouteGroup(
            name="Future Combined Route Group", drive_date=datetime(2099, 1, 1)
        )
        test_session.add(route_group)
        test_session.add_all(
            [
                active_school_location,
                active_family_location,
                unscheduled_school_location,
            ]
        )
        await test_session.commit()
        await test_session.refresh(route_group)
        await test_session.refresh(active_school_location)
        await test_session.refresh(active_family_location)
        await test_session.refresh(unscheduled_school_location)

        school_route = Route(
            name="Future School Route",
            length=1.0,
            route_group_id=route_group.route_group_id,
        )
        family_route = Route(
            name="Future Family Route",
            length=1.0,
            route_group_id=route_group.route_group_id,
        )
        test_session.add_all([school_route, family_route])
        await test_session.commit()
        await test_session.refresh(school_route)
        await test_session.refresh(family_route)

        test_session.add_all(
            [
                RouteStop(
                    route_id=school_route.route_id,
                    location_id=active_school_location.location_id,
                    stop_number=1,
                ),
                RouteStop(
                    route_id=family_route.route_id,
                    location_id=active_family_location.location_id,
                    stop_number=1,
                ),
            ]
        )
        await test_session.commit()

        response = await async_client.get(
            "/locations/", params={"delivery_type": "School", "status": "Active"}
        )

        assert response.status_code == 200
        location_ids = {loc["location_id"] for loc in response.json()["items"]}
        assert str(active_school_location.location_id) in location_ids
        assert str(active_family_location.location_id) not in location_ids
        assert str(unscheduled_school_location.location_id) not in location_ids

    @pytest.mark.asyncio
    async def test_get_locations_filters_by_location_group_delivery_type_and_status(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_location_group: Any,
    ) -> None:
        """GET /locations composes location_group_id with existing filters."""
        other_group = LocationGroup(name="Composed Other Group", color="#00AAFF")
        matching_location = Location(
            location_group_id=test_location_group.location_group_id,
            name="Matching School",
            contact_name="Matching School",
            address="1 Matching St",
            phone_primary="5551111111",
            delivery_type="School",
            in_roster=True,
        )
        wrong_type_location = Location(
            location_group_id=test_location_group.location_group_id,
            name="Wrong Type Family",
            contact_name="Wrong Type Family",
            address="1 Wrong Type St",
            phone_primary="5552222222",
            delivery_type="Family",
            in_roster=True,
        )
        wrong_group_location = Location(
            location_group_id=other_group.location_group_id,
            name="Wrong Group School",
            contact_name="Wrong Group School",
            address="1 Wrong Group St",
            phone_primary="5553333333",
            delivery_type="School",
            in_roster=True,
        )
        inactive_location = Location(
            location_group_id=test_location_group.location_group_id,
            name="Inactive School",
            contact_name="Inactive School",
            address="1 Inactive St",
            phone_primary="5554444444",
            delivery_type="School",
            in_roster=False,
        )
        test_session.add(other_group)
        test_session.add_all(
            [
                matching_location,
                wrong_type_location,
                wrong_group_location,
                inactive_location,
            ]
        )
        await test_session.commit()
        await test_session.refresh(matching_location)
        await test_session.refresh(wrong_type_location)
        await test_session.refresh(wrong_group_location)
        await test_session.refresh(inactive_location)

        response = await async_client.get(
            "/locations/",
            params={
                "location_group_id": str(test_location_group.location_group_id),
                "delivery_type": "School",
                "status": "Unscheduled",
            },
        )

        assert response.status_code == 200
        location_ids = {loc["location_id"] for loc in response.json()["items"]}
        assert str(matching_location.location_id) in location_ids
        assert str(wrong_type_location.location_id) not in location_ids
        assert str(wrong_group_location.location_id) not in location_ids
        assert str(inactive_location.location_id) not in location_ids

    @pytest.mark.asyncio
    async def test_get_locations_location_group_filter_preserves_pagination(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_location_group: Any,
    ) -> None:
        """GET /locations paginates after filtering by location_group_id."""
        other_group = LocationGroup(name="Pagination Other Group", color="#AA00FF")
        target_locations = [
            Location(
                location_group_id=test_location_group.location_group_id,
                name=f"Paged Family {index}",
                contact_name=f"Paged Family {index}",
                address=f"{index} Paged St",
                phone_primary=f"555111111{index}",
                delivery_type="Family",
                in_roster=True,
            )
            for index in range(3)
        ]
        other_location = Location(
            location_group_id=other_group.location_group_id,
            name="Excluded Paged Family",
            contact_name="Excluded Paged Family",
            address="1 Excluded Paged St",
            phone_primary="5552222222",
            delivery_type="Family",
            in_roster=True,
        )
        test_session.add(other_group)
        test_session.add_all([*target_locations, other_location])
        await test_session.commit()

        response = await async_client.get(
            "/locations/",
            params={
                "location_group_id": str(test_location_group.location_group_id),
                "page": 1,
                "page_size": 2,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] == 2
        assert {item["location_group_id"] for item in data["items"]} == {
            str(test_location_group.location_group_id)
        }

    @pytest.mark.asyncio
    async def test_get_location_by_id(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """Test GET /locations/{location_id} returns specific location."""
        # Create a location first
        create_response = await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "location_group_id": str(test_location_group.location_group_id),
            },
        )
        location_id = create_response.json()["location_id"]

        # Get the location by ID
        response = await async_client.get(f"/locations/{location_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["location_id"] == location_id
        assert data["contact_name"] == sample_location_data["contact_name"]

    @pytest.mark.asyncio
    async def test_get_location_not_found(self, async_client: AsyncClient) -> None:
        """Test GET /locations/{location_id} returns 404 for non-existent location."""
        fake_id = uuid4()
        response = await async_client.get(f"/locations/{fake_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_location(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """Test PATCH /locations/{location_id} updates a location."""
        # Create a location first
        create_response = await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "location_group_id": str(test_location_group.location_group_id),
            },
        )
        location_id = create_response.json()["location_id"]

        # Update the location
        update_data = {"dietary_restrictions": "No shellfish"}
        response = await async_client.patch(
            f"/locations/{location_id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["dietary_restrictions"] == "No shellfish"

    @pytest.mark.asyncio
    async def test_update_location_rejects_unknown_delivery_type(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """PATCH /locations/{id} validates delivery_type against settings."""
        create_response = await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "location_group_id": str(test_location_group.location_group_id),
            },
        )
        assert create_response.status_code == 201
        location_id = create_response.json()["location_id"]

        response = await async_client.patch(
            f"/locations/{location_id}", json={"delivery_type": "Unknown"}
        )

        assert response.status_code == 400
        assert "Unknown delivery_type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_ingest_locations_rejects_unknown_delivery_type(
        self, async_client: AsyncClient
    ) -> None:
        """POST /locations/ingest validates delivery_type against settings."""
        response = await async_client.post(
            "/locations/ingest",
            json={"delivery_type": "Unknown", "net_new": [], "stale": []},
        )

        assert response.status_code == 400
        assert "Unknown delivery_type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_location_clears_nullable_fields(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """Test PATCH /locations/{location_id} clears explicit null values."""
        create_response = await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "phone_secondary": "555-222-3333",
                "location_group_id": str(test_location_group.location_group_id),
            },
        )
        location_id = create_response.json()["location_id"]

        response = await async_client.patch(
            f"/locations/{location_id}", json={"phone_secondary": None}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["phone_secondary"] is None

    @pytest.mark.asyncio
    async def test_delete_location(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """Test DELETE /locations/{location_id} deletes a location."""
        # Create a location first
        create_response = await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "location_group_id": str(test_location_group.location_group_id),
            },
        )
        location_id = create_response.json()["location_id"]

        # Delete the location
        response = await async_client.delete(f"/locations/{location_id}")
        assert response.status_code == 204

        # Verify deletion
        get_response = await async_client.get(f"/locations/{location_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_locations_includes_group_name(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """GET /locations (list + single) exposes location_group_name. Both
        paths must eager-load location_group, else reading the name lazy-loads
        and 500s on the async session."""
        create_response = await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "location_group_id": str(test_location_group.location_group_id),
            },
        )
        assert create_response.status_code == 201
        location_id = create_response.json()["location_id"]

        listing = await async_client.get("/locations/")
        item = next(
            i for i in listing.json()["items"] if i["location_id"] == location_id
        )
        assert item["location_group_name"] == test_location_group.name

        single = await async_client.get(f"/locations/{location_id}")
        assert single.status_code == 200
        assert single.json()["location_group_name"] == test_location_group.name

    @pytest.mark.asyncio
    async def test_delete_all_locations(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """DELETE /locations removes every location (bulk destructive)."""
        for i in range(2):
            resp = await async_client.post(
                "/locations/",
                json={
                    **sample_location_data,
                    "contact_name": f"Contact {i}",
                    "location_group_id": str(test_location_group.location_group_id),
                },
            )
            assert resp.status_code == 201

        delete_response = await async_client.delete("/locations/")
        assert delete_response.status_code == 204

        listing = await async_client.get("/locations/")
        assert listing.json()["items"] == []
        assert listing.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_get_locations_returns_aggregate_fields(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """GET /locations includes assigned_route, last_delivery_date, total_deliveries."""
        create_resp = await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "location_group_id": str(test_location_group.location_group_id),
            },
        )
        assert create_resp.status_code == 201

        response = await async_client.get("/locations/")
        assert response.status_code == 200
        loc = response.json()["items"][0]
        assert loc["assigned_route"] is None
        assert loc["last_delivery_date"] is None
        assert loc["total_deliveries"] == 0

    @pytest.mark.asyncio
    async def test_get_location_by_id_returns_aggregate_fields(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """GET /locations/{id} includes assigned_route, last_delivery_date, total_deliveries."""
        create_resp = await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "location_group_id": str(test_location_group.location_group_id),
            },
        )
        assert create_resp.status_code == 201
        loc_id = create_resp.json()["location_id"]

        response = await async_client.get(f"/locations/{loc_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["assigned_route"] is None
        assert data["last_delivery_date"] is None
        assert data["total_deliveries"] == 0

    @pytest.mark.asyncio
    async def test_location_aggregates_with_completed_delivery(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_location_group: Any,
    ) -> None:
        """Completed delivery (RouteStopSnapshot exists) populates total_deliveries and last_delivery_date."""
        loc = Location(
            location_group_id=test_location_group.location_group_id,
            name="Delivered Family",
            contact_name="Delivered Family",
            address="10 Delivered St",
            phone_primary="5559999999",
            delivery_type="Family",
            in_roster=True,
        )
        past_group = RouteGroup(
            name="Past Route Group", drive_date=datetime(2024, 6, 1)
        )
        test_session.add_all([loc, past_group])
        await test_session.commit()
        await test_session.refresh(loc)
        await test_session.refresh(past_group)

        route = Route(
            name="Past Route", length=1.0, route_group_id=past_group.route_group_id
        )
        test_session.add(route)
        await test_session.commit()
        await test_session.refresh(route)

        stop = RouteStop(
            route_id=route.route_id,
            location_id=loc.location_id,
            stop_number=1,
        )
        test_session.add(stop)
        await test_session.commit()
        await test_session.refresh(stop)

        snapshot = RouteStopSnapshot(
            route_stop_id=stop.route_stop_id,
            address="10 Delivered St",
            contact_name="Delivered Family",
            phone_primary="5559999999",
            num_children=2,
            latitude=0.0,
            longitude=0.0,
        )
        test_session.add(snapshot)
        await test_session.commit()

        response = await async_client.get(f"/locations/{loc.location_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_deliveries"] == 1
        assert data["last_delivery_date"] is not None
        assert data["last_delivery_date"].startswith("2024-06-01")
        assert data["assigned_route"] is None

    @pytest.mark.asyncio
    async def test_location_aggregates_with_assigned_route(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_location_group: Any,
    ) -> None:
        """Upcoming route (no snapshot) populates assigned_route but not delivery aggregates."""
        loc = Location(
            location_group_id=test_location_group.location_group_id,
            name="Upcoming Family",
            contact_name="Upcoming Family",
            address="20 Upcoming St",
            phone_primary="5558888888",
            delivery_type="Family",
            in_roster=True,
        )
        future_group = RouteGroup(
            name="Future Route Group", drive_date=datetime(2099, 7, 1)
        )
        test_session.add_all([loc, future_group])
        await test_session.commit()
        await test_session.refresh(loc)
        await test_session.refresh(future_group)

        route = Route(
            name="Future Route Alpha",
            length=1.0,
            route_group_id=future_group.route_group_id,
        )
        test_session.add(route)
        await test_session.commit()
        await test_session.refresh(route)

        test_session.add(
            RouteStop(
                route_id=route.route_id,
                location_id=loc.location_id,
                stop_number=1,
            )
        )
        await test_session.commit()

        response = await async_client.get(f"/locations/{loc.location_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["assigned_route"] == "Future Route Alpha"
        assert data["total_deliveries"] == 0
        assert data["last_delivery_date"] is None

    @pytest.mark.asyncio
    async def test_location_assigned_route_picks_soonest(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_location_group: Any,
    ) -> None:
        """When a location is on multiple upcoming routes, assigned_route is the soonest."""
        loc = Location(
            location_group_id=test_location_group.location_group_id,
            name="Multi Route Family",
            contact_name="Multi Route Family",
            address="30 Multi St",
            phone_primary="5557777777",
            delivery_type="Family",
            in_roster=True,
        )
        sooner_group = RouteGroup(name="Sooner Group", drive_date=datetime(2098, 1, 1))
        later_group = RouteGroup(name="Later Group", drive_date=datetime(2099, 1, 1))
        test_session.add_all([loc, sooner_group, later_group])
        await test_session.commit()
        await test_session.refresh(loc)
        await test_session.refresh(sooner_group)
        await test_session.refresh(later_group)

        sooner_route = Route(
            name="Sooner Route",
            length=1.0,
            route_group_id=sooner_group.route_group_id,
        )
        later_route = Route(
            name="Later Route",
            length=1.0,
            route_group_id=later_group.route_group_id,
        )
        test_session.add_all([sooner_route, later_route])
        await test_session.commit()
        await test_session.refresh(sooner_route)
        await test_session.refresh(later_route)

        test_session.add_all(
            [
                RouteStop(
                    route_id=sooner_route.route_id,
                    location_id=loc.location_id,
                    stop_number=1,
                ),
                RouteStop(
                    route_id=later_route.route_id,
                    location_id=loc.location_id,
                    stop_number=1,
                ),
            ]
        )
        await test_session.commit()

        response = await async_client.get(f"/locations/{loc.location_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["assigned_route"] == "Sooner Route"


class TestLocationImportRoutes:
    """Test suite for location import validation, review, and ingest."""

    @pytest.mark.asyncio
    async def test_review_locations_emits_specific_blocking_alerts(
        self, client_with_overrides: Any
    ) -> None:
        fake_maps = FakeGoogleMapsClient()
        async_client = await client_with_overrides(
            {get_google_maps_client: lambda: fake_maps}
        )
        request = import_review_request(
            [
                {"Name": "", "Address": "", "Delivery Group": "", "Phone": ""},
                {
                    "Name": "12345",
                    "Address": "1 Valid St",
                    "Delivery Group": "Monday",
                    "Phone": "+14164164168",
                },
                {
                    "Name": "Invalid Address Family",
                    "Address": "Invalid Address",
                    "Delivery Group": "Monday",
                    "Phone": "+14164164169",
                },
                {
                    "Name": "Invalid Phone Family",
                    "Address": "2 Valid St",
                    "Delivery Group": "Monday",
                    "Phone": "not-a-phone",
                },
            ]
        )

        response = await async_client.post("/locations/review", **request)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is False
        assert set(body["rows"][0]["alerts"]) == {
            "MISSING_NAME",
            "MISSING_ADDRESS",
            "MISSING_DELIVERY_GROUP",
            "MISSING_PHONE_NUMBER",
        }
        assert body["rows"][1]["alerts"] == ["INVALID_NAME"]
        assert body["rows"][2]["alerts"] == ["INVALID_ADDRESS"]
        assert body["rows"][3]["alerts"] == ["INVALID_PHONE_NUMBER"]
        assert fake_maps.calls == ["1 Valid St", "Invalid Address", "2 Valid St"]

    @pytest.mark.asyncio
    async def test_review_locations_detects_duplicate_groups_by_two_of_three(
        self, client_with_overrides: Any
    ) -> None:
        fake_maps = FakeGoogleMapsClient()
        async_client = await client_with_overrides(
            {get_google_maps_client: lambda: fake_maps}
        )
        request = import_review_request(
            [
                {
                    "Name": "Same Name Address",
                    "Address": "10 Match St",
                    "Delivery Group": "Monday",
                    "Phone": "+14164164168",
                },
                {
                    "Name": "Same Name Address",
                    "Address": "10 Match St",
                    "Delivery Group": "Monday",
                    "Phone": "+14164164169",
                },
                {
                    "Name": "Same Name Phone",
                    "Address": "11 Match St",
                    "Delivery Group": "Monday",
                    "Phone": "+14164164170",
                },
                {
                    "Name": "Same Name Phone",
                    "Address": "12 Changed St",
                    "Delivery Group": "Monday",
                    "Phone": "+14164164170",
                },
                {
                    "Name": "Same Address Phone A",
                    "Address": "13 Match St",
                    "Delivery Group": "Monday",
                    "Phone": "+14165550100",
                },
                {
                    "Name": "Same Address Phone B",
                    "Address": "13 Match St",
                    "Delivery Group": "Monday",
                    "Phone": "+14165550100",
                },
                {
                    "Name": "Exact Duplicate",
                    "Address": "14 Match St",
                    "Delivery Group": "Monday",
                    "Phone": "+15195550123",
                },
                {
                    "Name": "Exact Duplicate",
                    "Address": "14 Match St",
                    "Delivery Group": "Monday",
                    "Phone": "+15195550123",
                },
                {
                    "Name": "Apartment A",
                    "Address": "15 Shared Building",
                    "Delivery Group": "Monday",
                    "Phone": "+14164164171",
                },
                {
                    "Name": "Apartment B",
                    "Address": "15 Shared Building",
                    "Delivery Group": "Monday",
                    "Phone": "+14164164172",
                },
            ]
        )

        response = await async_client.post("/locations/review", **request)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is False
        assert body["duplicate_groups"] == [
            {"rows": [1, 2], "matching_fields": ["address", "contact_name"]},
            {"rows": [3, 4], "matching_fields": ["contact_name", "phone_primary"]},
            {"rows": [5, 6], "matching_fields": ["address", "phone_primary"]},
            {
                "rows": [7, 8],
                "matching_fields": ["address", "contact_name", "phone_primary"],
            },
        ]
        duplicate_rows = {
            row["row"] for row in body["rows"] if "LOCAL_DUPLICATE" in row["alerts"]
        }
        assert duplicate_rows == {1, 2, 3, 4, 5, 6, 7, 8}
        assert body["rows"][8]["alerts"] == []
        assert body["rows"][9]["alerts"] == []

    @pytest.mark.asyncio
    async def test_review_locations_classifies_import_rows_with_two_of_three_matching(
        self,
        client_with_overrides: Any,
        test_session: AsyncSession,
        test_location_group: Any,
    ) -> None:
        fake_maps = FakeGoogleMapsClient()
        async_client = await client_with_overrides(
            {get_google_maps_client: lambda: fake_maps}
        )
        stale_group = LocationGroup(name="Stale Group", color="#222222", notes="")
        test_session.add(stale_group)
        test_session.add_all(
            [
                Location(
                    location_group_id=test_location_group.location_group_id,
                    name="Exact Family",
                    contact_name="Exact Family",
                    address="Formatted 1 Main St",
                    phone_primary="+14164164168",
                    num_children=1,
                    delivery_type="Family",
                ),
                Location(
                    location_group_id=test_location_group.location_group_id,
                    name="Address Change Family",
                    contact_name="Address Change Family",
                    address="Formatted Old Address",
                    phone_primary="+14164164169",
                    num_children=2,
                    delivery_type="Family",
                ),
                Location(
                    location_group_id=test_location_group.location_group_id,
                    name="Phone Change Family",
                    contact_name="Phone Change Family",
                    address="Formatted 3 Main St",
                    phone_primary="+14164164170",
                    num_children=3,
                    delivery_type="Family",
                ),
                Location(
                    location_group_id=stale_group.location_group_id,
                    name="Stale Family",
                    contact_name="Stale Family",
                    address="Formatted 9 Main St",
                    phone_primary="+14165550100",
                    num_children=4,
                    delivery_type="Family",
                ),
            ]
        )
        await test_session.commit()

        request = import_review_request(
            [
                {
                    "Name": "Exact Family",
                    "Address": "1 Main St",
                    "Delivery Group": test_location_group.name,
                    "Phone": "+14164164168",
                    "Children": "1",
                },
                {
                    "Name": "Address Change Family",
                    "Address": "New Address",
                    "Delivery Group": test_location_group.name,
                    "Phone": "+14164164169",
                    "Children": "2",
                },
                {
                    "Name": "Phone Change Family",
                    "Address": "3 Main St",
                    "Delivery Group": test_location_group.name,
                    "Phone": "+15195550123",
                    "Children": "3",
                },
                {
                    "Name": "Net New Family",
                    "Address": "4 Main St",
                    "Delivery Group": "New Group",
                    "Phone": "+14164164171",
                    "Children": "5",
                },
            ]
        )

        response = await async_client.post("/locations/review", **request)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert [entry["contact_name"] for entry in body["net_new"]] == [
            "Net New Family"
        ]
        assert [entry["contact_name"] for entry in body["stale"]] == ["Stale Family"]
        changed_by_name = {entry["contact_name"]: entry for entry in body["changed"]}
        assert set(changed_by_name) == {
            "Address Change Family",
            "Phone Change Family",
        }
        assert changed_by_name["Address Change Family"]["address"] == {
            "new_value": "Formatted New Address",
            "old_value": "Formatted Old Address",
        }
        assert changed_by_name["Phone Change Family"]["phone_primary"] == {
            "new_value": "+15195550123",
            "old_value": "+14164164170",
        }

    @pytest.mark.asyncio
    async def test_review_locations_blank_children_does_not_mark_changed(
        self,
        client_with_overrides: Any,
        test_session: AsyncSession,
        test_location_group: Any,
    ) -> None:
        fake_maps = FakeGoogleMapsClient()
        async_client = await client_with_overrides(
            {get_google_maps_client: lambda: fake_maps}
        )
        test_session.add(
            Location(
                location_group_id=test_location_group.location_group_id,
                name="Blank Children Family",
                contact_name="Blank Children Family",
                address="Formatted 22 Main St",
                phone_primary="+14164164168",
                num_children=7,
                delivery_type="Family",
            )
        )
        await test_session.commit()

        request = import_review_request(
            [
                {
                    "Name": "Blank Children Family",
                    "Address": "22 Main St",
                    "Delivery Group": test_location_group.name,
                    "Phone": "+14164164168",
                    "Children": "",
                }
            ]
        )

        response = await async_client.post("/locations/review", **request)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["changed"] == []
        assert body["net_new"] == []
        assert body["stale"] == []

    @pytest.mark.asyncio
    async def test_review_locations_claims_existing_matches_once(
        self,
        client_with_overrides: Any,
        test_session: AsyncSession,
        test_location_group: Any,
    ) -> None:
        fake_maps = FakeGoogleMapsClient()
        async_client = await client_with_overrides(
            {get_google_maps_client: lambda: fake_maps}
        )
        test_session.add(
            Location(
                location_group_id=test_location_group.location_group_id,
                name="Shared Match",
                contact_name="Shared Match",
                address="Formatted 44 Main St",
                phone_primary="+14164164168",
                num_children=2,
                delivery_type="Family",
            )
        )
        await test_session.commit()

        request = import_review_request(
            [
                {
                    "Name": "Shared Match",
                    "Address": "44 Main St",
                    "Delivery Group": test_location_group.name,
                    "Phone": "+14164164169",
                    "Children": "2",
                },
                {
                    "Name": "Different Name",
                    "Address": "44 Main St",
                    "Delivery Group": test_location_group.name,
                    "Phone": "+14164164168",
                    "Children": "2",
                },
            ]
        )

        response = await async_client.post("/locations/review", **request)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert len(body["changed"]) == 1
        assert len(body["net_new"]) == 1

    @pytest.mark.asyncio
    async def test_review_locations_revives_previously_stale_location(
        self,
        client_with_overrides: Any,
        test_session: AsyncSession,
        test_location_group: Any,
    ) -> None:
        fake_maps = FakeGoogleMapsClient()
        async_client = await client_with_overrides(
            {get_google_maps_client: lambda: fake_maps}
        )
        stale_location = Location(
            location_group_id=test_location_group.location_group_id,
            name="Returning Family",
            contact_name="Returning Family",
            address="Formatted 55 Main St",
            phone_primary="+14164164168",
            num_children=3,
            delivery_type="Family",
            in_roster=False,
        )
        test_session.add(stale_location)
        await test_session.commit()

        request = import_review_request(
            [
                {
                    "Name": "Returning Family",
                    "Address": "55 Main St",
                    "Delivery Group": test_location_group.name,
                    "Phone": "+14164164168",
                    "Children": "3",
                }
            ]
        )

        response = await async_client.post("/locations/review", **request)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["net_new"] == []
        assert body["stale"] == []
        assert len(body["changed"]) == 1
        assert body["changed"][0]["location_id"] == str(stale_location.location_id)

    @pytest.mark.asyncio
    async def test_ingest_locations_applies_stale_and_changed_rows(
        self,
        client_with_overrides: Any,
        test_session: AsyncSession,
        test_location_group: Any,
    ) -> None:
        from sqlmodel import select

        from app.models.note import Note
        from app.models.note_chain import NoteChain

        review_maps = FakeGoogleMapsClient()
        async_client = await client_with_overrides(
            {get_google_maps_client: lambda: review_maps}
        )
        note_chain = NoteChain()
        test_session.add(note_chain)
        await test_session.flush()
        existing_note = Note(
            note_chain_id=note_chain.note_chain_id,
            message="keep this note history",
        )
        test_session.add(existing_note)
        address_change = Location(
            location_group_id=test_location_group.location_group_id,
            name="Address Change Family",
            contact_name="Address Change Family",
            address="Formatted Old Address",
            phone_primary="+14164164169",
            num_children=2,
            delivery_type="Family",
            note_chain_id=note_chain.note_chain_id,
        )
        phone_change = Location(
            location_group_id=test_location_group.location_group_id,
            name="Phone Change Family",
            contact_name="Phone Change Family",
            address="Formatted 3 Main St",
            phone_primary="+14164164170",
            num_children=3,
            delivery_type="Family",
        )
        stale = Location(
            location_group_id=test_location_group.location_group_id,
            name="Stale Family",
            contact_name="Stale Family",
            address="Formatted 9 Main St",
            phone_primary="+14165550100",
            num_children=4,
            delivery_type="Family",
        )
        test_session.add_all([address_change, phone_change, stale])
        await test_session.commit()

        review_request = import_review_request(
            [
                {
                    "Name": "Address Change Family",
                    "Address": "New Address",
                    "Delivery Group": test_location_group.name,
                    "Phone": "+14164164169",
                    "Children": "2",
                },
                {
                    "Name": "Phone Change Family",
                    "Address": "3 Main St",
                    "Delivery Group": test_location_group.name,
                    "Phone": "+15195550123",
                    "Children": "3",
                },
                {
                    "Name": "Net New Family",
                    "Address": "4 Main St",
                    "Delivery Group": "New Group",
                    "Phone": "+14164164171",
                    "Children": "5",
                },
            ]
        )
        review_response = await async_client.post("/locations/review", **review_request)
        assert review_response.status_code == 200
        review_body = review_response.json()

        ingest_maps = FakeGoogleMapsClient()
        ingest_client = await client_with_overrides(
            {get_google_maps_client: lambda: ingest_maps}
        )
        ingest_payload = {
            "delivery_type": "Family",
            "net_new": [
                {
                    "contact_name": entry["contact_name"],
                    "address": entry["address"],
                    "delivery_group": entry["delivery_group"],
                    "phone_primary": entry["phone_primary"],
                    "phone_secondary": entry["phone_secondary"],
                    "num_children": entry["num_children"],
                }
                for entry in review_body["net_new"]
            ],
            "stale": review_body["stale"],
            "changed": review_body["changed"],
        }

        ingest_response = await ingest_client.post(
            "/locations/ingest", json=ingest_payload
        )

        assert ingest_response.status_code == 200
        assert ingest_maps.calls == ["Formatted 4 Main St", "Formatted New Address"]
        body = ingest_response.json()
        assert len(body["created"]) == 2
        assert len(body["archived"]) == 2

        await test_session.refresh(address_change)
        await test_session.refresh(phone_change)
        await test_session.refresh(stale)
        assert address_change.in_roster is False
        assert stale.in_roster is False
        assert phone_change.in_roster is True
        assert phone_change.phone_primary == "+15195550123"

        result = await test_session.execute(
            select(Location).where(Location.contact_name == "Address Change Family")
        )
        address_change_locations = list(result.scalars().all())
        replacement = next(
            loc
            for loc in address_change_locations
            if loc.location_id != address_change.location_id
        )
        assert replacement.in_roster is True
        assert replacement.note_chain_id == note_chain.note_chain_id
        assert replacement.address == "Formatted New Address"
        retained_note = await test_session.get(Note, existing_note.note_id)
        assert retained_note is not None
        assert retained_note.note_chain_id == replacement.note_chain_id

    @pytest.mark.asyncio
    async def test_ingest_locations_rejects_duplicate_changed_location_ids(
        self,
        async_client: AsyncClient,
        test_location_group: Any,
    ) -> None:
        location_id = uuid4()
        changed_entry = {
            "row": 1,
            "location_id": str(location_id),
            "contact_name": "Duplicate Change",
            "address": "Formatted 1 Main St",
            "delivery_group": test_location_group.name,
            "phone_primary": "+14164164168",
            "phone_secondary": None,
            "num_children": 1,
        }

        response = await async_client.post(
            "/locations/ingest",
            json={
                "delivery_type": "Family",
                "net_new": [],
                "stale": [],
                "changed": [changed_entry, changed_entry],
            },
        )

        assert response.status_code == 400
        assert "only be included once" in response.json()["detail"]


class TestLocationGroupRoutes:
    """Test suite for location group API routes."""

    @pytest.mark.asyncio
    async def test_get_location_groups_empty(self, async_client: AsyncClient) -> None:
        """GET /location-groups returns an empty list when none exist."""
        response = await async_client.get("/location-groups/")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_create_location_group_links_locations(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        sample_location_group_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """POST /location-groups creates a group, links (reassigns) the given
        locations, and returns an accurate num_locations.

        Regression test for the 500 from reading the computed num_locations off
        a lazily-loaded relationship on the async session, and for the FK
        actually being updated to the new group.
        """
        # Create two locations (each starts in the bootstrap group)
        location_ids = []
        for i in range(2):
            data = {
                **sample_location_data,
                "contact_name": f"Contact {i}",
                "location_group_id": str(test_location_group.location_group_id),
            }
            create_response = await async_client.post("/locations/", json=data)
            assert create_response.status_code == 201
            location_ids.append(create_response.json()["location_id"])

        # Create a new group that takes over those locations
        response = await async_client.post(
            "/location-groups/",
            json={**sample_location_group_data, "location_ids": location_ids},
        )
        assert response.status_code == 201
        group = response.json()
        assert group["name"] == sample_location_group_data["name"]
        assert group["num_locations"] == 2

        # Each location now reports the new group via its FK
        for location_id in location_ids:
            loc = (await async_client.get(f"/locations/{location_id}")).json()
            assert loc["location_group_id"] == group["location_group_id"]

    @pytest.mark.asyncio
    async def test_create_location_group_requires_location_ids(
        self,
        async_client: AsyncClient,
        sample_location_group_data: dict[str, Any],
    ) -> None:
        """POST /location-groups rejects an empty location_ids list."""
        response = await async_client.post(
            "/location-groups/",
            json={**sample_location_group_data, "location_ids": []},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_location_groups_with_data(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """GET /location-groups returns groups with num_locations populated."""
        await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "location_group_id": str(test_location_group.location_group_id),
            },
        )

        response = await async_client.get("/location-groups/")
        assert response.status_code == 200
        groups = response.json()
        assert len(groups) == 1
        assert groups[0]["location_group_id"] == str(
            test_location_group.location_group_id
        )
        assert groups[0]["num_locations"] == 1

    @pytest.mark.asyncio
    async def test_create_location_group_skips_unknown_location_id(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        sample_location_group_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """Unknown location_ids are warned and skipped, not fatal — the group
        is still created and links only the locations that exist."""
        create_response = await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "location_group_id": str(test_location_group.location_group_id),
            },
        )
        location_id = create_response.json()["location_id"]
        unknown_id = str(uuid4())

        response = await async_client.post(
            "/location-groups/",
            json={
                **sample_location_group_data,
                "location_ids": [location_id, unknown_id],
            },
        )
        assert response.status_code == 201
        # Only the real location was linked
        assert response.json()["num_locations"] == 1

    @pytest.mark.asyncio
    async def test_create_location_group_reassigns_existing_location(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        sample_location_group_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """A location is moved from its current group to a new group when the
        new group's create references it (and the old group loses it)."""
        create_response = await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "location_group_id": str(test_location_group.location_group_id),
            },
        )
        location_id = create_response.json()["location_id"]

        group_b = (
            await async_client.post(
                "/location-groups/",
                json={
                    **sample_location_group_data,
                    "name": "Group B",
                    "location_ids": [location_id],
                },
            )
        ).json()

        # The location now points at B, and B reports it
        assert group_b["num_locations"] == 1
        loc = (await async_client.get(f"/locations/{location_id}")).json()
        assert loc["location_group_id"] == group_b["location_group_id"]

        # The original (bootstrap) group no longer counts it
        groups = {
            g["location_group_id"]: g
            for g in (await async_client.get("/location-groups/")).json()
        }
        assert groups[str(test_location_group.location_group_id)]["num_locations"] == 0
        assert groups[group_b["location_group_id"]]["num_locations"] == 1

    @pytest.mark.asyncio
    async def test_update_location_group(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """PATCH /location-groups/{id} updates fields and returns the group
        with num_locations populated (regression: previously 500'd reading the
        lazily-loaded num_locations)."""
        await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "location_group_id": str(test_location_group.location_group_id),
            },
        )

        response = await async_client.patch(
            f"/location-groups/{test_location_group.location_group_id}",
            json={"name": "Renamed Group"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Renamed Group"
        assert data["num_locations"] == 1

    @pytest.mark.asyncio
    async def test_update_location_group_not_found(
        self, async_client: AsyncClient
    ) -> None:
        """PATCH /location-groups/{id} returns 404 for a non-existent group."""
        response = await async_client.patch(
            f"/location-groups/{uuid4()}", json={"name": "Nope"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_empty_location_group(
        self, async_client: AsyncClient, test_location_group: Any
    ) -> None:
        """DELETE /location-groups/{id} removes a group that has no locations."""
        response = await async_client.delete(
            f"/location-groups/{test_location_group.location_group_id}"
        )
        assert response.status_code == 204
        assert (await async_client.get("/location-groups/")).json() == []

    @pytest.mark.asyncio
    async def test_delete_location_group_with_locations_conflicts(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """DELETE /location-groups/{id} returns 409 when the group still has
        locations — they require a group, so can't be orphaned."""
        await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "location_group_id": str(test_location_group.location_group_id),
            },
        )
        response = await async_client.delete(
            f"/location-groups/{test_location_group.location_group_id}"
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_get_location_group_by_id(
        self, async_client: AsyncClient, test_location_group: Any
    ) -> None:
        """GET /location-groups/{id} returns the group."""
        response = await async_client.get(
            f"/location-groups/{test_location_group.location_group_id}"
        )
        assert response.status_code == 200
        assert response.json()["location_group_id"] == str(
            test_location_group.location_group_id
        )

    @pytest.mark.asyncio
    async def test_get_location_group_not_found(
        self, async_client: AsyncClient
    ) -> None:
        """GET /location-groups/{id} returns 404 for an unknown id."""
        response = await async_client.get(f"/location-groups/{uuid4()}")
        assert response.status_code == 404


class TestRouteRoutes:
    """Test suite for route API routes."""

    @pytest.mark.asyncio
    async def test_get_routes_empty(self, async_client: AsyncClient) -> None:
        """Test GET /routes returns empty paginated response when no routes exist."""
        response = await async_client.get("/routes")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["total_pages"] == 0

    @pytest.mark.asyncio
    async def test_get_routes_with_data(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_route: Any,
        test_location_group: Any,
    ) -> None:
        """Test GET /routes returns paginated list of routes."""
        from app.models.location import Location
        from app.models.route_stop import RouteStop

        loc_a = Location(
            location_group_id=test_location_group.location_group_id,
            name="Route Stop A",
            contact_name="Route Stop A",
            address="1 Route St",
            phone_primary="5550000001",
            num_children=6,
            delivery_type="Family",
        )
        loc_b = Location(
            location_group_id=test_location_group.location_group_id,
            name="Route Stop B",
            contact_name="Route Stop B",
            address="2 Route St",
            phone_primary="5550000002",
            num_children=10,
            delivery_type="Family",
        )
        test_session.add_all([loc_a, loc_b])
        await test_session.commit()
        await test_session.refresh(loc_a)
        await test_session.refresh(loc_b)
        test_session.add_all(
            [
                RouteStop(
                    route_id=test_route.route_id,
                    location_id=loc_a.location_id,
                    stop_number=1,
                ),
                RouteStop(
                    route_id=test_route.route_id,
                    location_id=loc_b.location_id,
                    stop_number=2,
                ),
            ]
        )
        await test_session.commit()

        # A second route in a later-dated group, to exercise drive_date ordering.
        later_group = RouteGroup(name="Later Group", drive_date=datetime(2024, 6, 1))
        test_session.add(later_group)
        await test_session.commit()
        await test_session.refresh(later_group)
        later_route = Route(
            name="Later Route",
            length=1.0,
            route_group_id=later_group.route_group_id,
        )
        test_session.add(later_route)
        await test_session.commit()
        await test_session.refresh(later_route)

        response = await async_client.get("/routes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)
        route = next(
            item
            for item in data["items"]
            if item["route_id"] == str(test_route.route_id)
        )
        assert route["num_stops"] == 2
        assert route["box_total"] == 8
        # List rows carry start_time (None until the route is scheduled).
        assert route["start_time"] is None

        # Default order is ascending by drive_date (oldest-first); the
        # earlier-dated test_route precedes the later one.
        asc_ids = [item["route_id"] for item in data["items"]]
        assert asc_ids.index(str(test_route.route_id)) < asc_ids.index(
            str(later_route.route_id)
        )

        # order=desc reverses it (most-recent-first), powering the past feed.
        desc = await async_client.get("/routes?order=desc")
        assert desc.status_code == 200
        desc_ids = [item["route_id"] for item in desc.json()["items"]]
        assert desc_ids.index(str(later_route.route_id)) < desc_ids.index(
            str(test_route.route_id)
        )

    @pytest.mark.asyncio
    async def test_get_routes_uses_snapshotted_box_totals_for_frozen_routes(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_location_group: Any,
    ) -> None:
        """GET /routes uses frozen stop snapshots for completed routes."""
        from app.models.location import Location
        from app.models.route import Route
        from app.models.route_group import RouteGroup
        from app.models.route_snapshot import RouteSnapshot
        from app.models.route_stop import RouteStop
        from app.models.route_stop_snapshot import RouteStopSnapshot

        past_group = RouteGroup(
            name="Past Route Group",
            notes="",
            drive_date=datetime.combine(
                date.today() - timedelta(days=7), datetime.min.time()
            ),
        )
        loc = Location(
            location_group_id=test_location_group.location_group_id,
            name="Frozen Stop",
            contact_name="Frozen Stop",
            address="1 Frozen St",
            phone_primary="5550000009",
            num_children=6,
            delivery_type="Family",
        )
        test_session.add_all([past_group, loc])
        await test_session.commit()
        await test_session.refresh(past_group)
        await test_session.refresh(loc)

        route = Route(
            name="Frozen Route",
            length=4.0,
            route_group_id=past_group.route_group_id,
        )
        test_session.add(route)
        await test_session.commit()
        await test_session.refresh(route)

        stop = RouteStop(
            route_id=route.route_id,
            location_id=loc.location_id,
            stop_number=1,
        )
        test_session.add(stop)
        await test_session.commit()
        await test_session.refresh(stop)

        test_session.add(
            RouteSnapshot(
                route_id=route.route_id,
                start_address="Warehouse",
                start_latitude=0.0,
                start_longitude=0.0,
            )
        )
        test_session.add(
            RouteStopSnapshot(
                route_stop_id=stop.route_stop_id,
                address=loc.address,
                contact_name=loc.contact_name,
                phone_primary=loc.phone_primary,
                num_children=8,
                latitude=loc.latitude or 0.0,
                longitude=loc.longitude or 0.0,
            )
        )
        await test_session.commit()

        # Mutate the live location after the route is frozen; the list should
        # still read the snapshotted count.
        loc.num_children = 1
        await test_session.commit()

        response = await async_client.get("/routes")
        assert response.status_code == 200
        data = response.json()
        route_item = next(
            item for item in data["items"] if item["route_id"] == str(route.route_id)
        )
        assert route_item["num_stops"] == 1
        assert route_item["box_total"] == 4

    @pytest.mark.asyncio
    async def test_get_route_by_id(
        self, async_client: AsyncClient, test_route: Any
    ) -> None:
        """GET /routes/{id} returns the route with an (empty) stops list."""
        response = await async_client.get(f"/routes/{test_route.route_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["route_id"] == str(test_route.route_id)
        assert body["stops"] == []
        # drive_date is sourced from the route's group; with no stops there's no
        # location to read a delivery_type from.
        assert body["drive_date"] is not None
        assert body["delivery_type"] is None

    @pytest.mark.asyncio
    async def test_get_route_by_id_embeds_ordered_stops(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_route: Any,
        test_location_group: Any,
    ) -> None:
        """GET /routes/{id} embeds stops in sequence order with per-stop detail,
        read live from Location for an upcoming route."""
        # Build locations directly (not via POST /locations, which geocodes the
        # address); attach a note chain to each so note_chain_id is populated.
        chain_a = NoteChain()
        chain_b = NoteChain()
        loc_a = Location(
            location_group_id=test_location_group.location_group_id,
            name="Stop A",
            contact_name="Alice",
            address="1 A St",
            phone_primary="5550000001",
            phone_secondary="5559999991",
            num_children=6,
            delivery_type="Family",
        )
        loc_b = Location(
            location_group_id=test_location_group.location_group_id,
            name="Stop B",
            contact_name="Bob",
            address="2 B St",
            phone_primary="5550000002",
            num_children=10,
            delivery_type="Family",
        )
        test_session.add_all([chain_a, chain_b, loc_a, loc_b])
        await test_session.commit()
        await test_session.refresh(chain_a)
        await test_session.refresh(chain_b)
        await test_session.refresh(loc_a)
        await test_session.refresh(loc_b)

        loc_a.note_chain_id = chain_a.note_chain_id
        loc_b.note_chain_id = chain_b.note_chain_id

        # Insert out of order to prove the response is sorted by stop_number.
        test_session.add_all(
            [
                RouteStop(
                    route_id=test_route.route_id,
                    location_id=loc_a.location_id,
                    stop_number=2,
                ),
                RouteStop(
                    route_id=test_route.route_id,
                    location_id=loc_b.location_id,
                    stop_number=1,
                ),
            ]
        )
        await test_session.commit()

        response = await async_client.get(f"/routes/{test_route.route_id}")
        assert response.status_code == 200
        body = response.json()
        stops = body["stops"]
        assert [s["stop_number"] for s in stops] == [1, 2]
        # drive_date from the group; delivery_type read from the stops' locations
        # (uniform across the route).
        assert body["drive_date"] is not None
        assert body["delivery_type"] == "Family"

        first, second = stops
        # Stop 1 -> loc_b
        assert first["address"] == "2 B St"
        assert first["contact_name"] == "Bob"
        assert first["phone_primary"] == "5550000002"
        assert first["phone_secondary"] is None
        assert first["boxes"] == 5  # ceil(10 / 2)
        assert first["note_chain_id"] == str(chain_b.note_chain_id)
        # Stop 2 -> loc_a
        assert second["address"] == "1 A St"
        assert second["phone_secondary"] == "5559999991"
        assert second["boxes"] == 3  # ceil(6 / 2)
        assert second["note_chain_id"] == str(chain_a.note_chain_id)

    @pytest.mark.asyncio
    async def test_get_route_by_id_uses_snapshot_for_frozen_stops(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_location_group: Any,
    ) -> None:
        """For a frozen (past) route, snapshotted stop fields (including both
        phone numbers) win over the mutated live Location; note_chain_id is
        live-only (note chains aren't snapshotted)."""
        note_chain = NoteChain()
        loc = Location(
            location_group_id=test_location_group.location_group_id,
            name="Frozen Fam",
            contact_name="Live Name",
            address="Live Addr",
            phone_primary="5550000000",
            phone_secondary="5551112222",
            num_children=2,
            delivery_type="Family",
        )
        past_group = RouteGroup(name="Past Group", drive_date=datetime(2024, 1, 1))
        test_session.add_all([note_chain, loc, past_group])
        await test_session.commit()
        await test_session.refresh(note_chain)
        await test_session.refresh(loc)
        await test_session.refresh(past_group)

        loc.note_chain_id = note_chain.note_chain_id
        await test_session.commit()

        route = Route(
            name="Frozen Route",
            length=2.0,
            route_group_id=past_group.route_group_id,
        )
        test_session.add(route)
        await test_session.commit()
        await test_session.refresh(route)

        stop = RouteStop(
            route_id=route.route_id,
            location_id=loc.location_id,
            stop_number=1,
        )
        test_session.add(stop)
        await test_session.commit()
        await test_session.refresh(stop)

        test_session.add(
            RouteStopSnapshot(
                route_stop_id=stop.route_stop_id,
                address="Frozen Addr",
                contact_name="Frozen Name",
                phone_primary="5557778888",
                phone_secondary="5557779999",
                num_children=8,
                latitude=0.0,
                longitude=0.0,
            )
        )
        await test_session.commit()

        # Mutate the live location after the freeze; the response must ignore it
        # for snapshotted fields (including phone_secondary).
        loc.address = "Changed Addr"
        loc.num_children = 1
        loc.phone_secondary = "5550009999"
        await test_session.commit()

        response = await async_client.get(f"/routes/{route.route_id}")
        assert response.status_code == 200
        stops = response.json()["stops"]
        assert len(stops) == 1
        stop_body = stops[0]
        assert stop_body["address"] == "Frozen Addr"
        assert stop_body["contact_name"] == "Frozen Name"
        assert stop_body["phone_primary"] == "5557778888"
        # Secondary phone is snapshotted -> frozen value, not the mutated live one.
        assert stop_body["phone_secondary"] == "5557779999"
        assert stop_body["boxes"] == 4  # ceil(8 / 2) from snapshot, not live 1
        # Note chains aren't snapshotted -> note_chain_id is read live.
        assert stop_body["note_chain_id"] == str(note_chain.note_chain_id)

    @pytest.mark.asyncio
    async def test_get_route_not_found(self, async_client: AsyncClient) -> None:
        """GET /routes/{id} returns 404 for an unknown route."""
        response = await async_client.get(f"/routes/{uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_route(
        self, async_client: AsyncClient, test_route: Any
    ) -> None:
        """DELETE /routes/{id} removes the route."""
        response = await async_client.delete(f"/routes/{test_route.route_id}")
        assert response.status_code == 204
        get_response = await async_client.get(f"/routes/{test_route.route_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_route_not_found(self, async_client: AsyncClient) -> None:
        """DELETE /routes/{id} returns 404 for an unknown route."""
        response = await async_client.delete(f"/routes/{uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_route_metadata(
        self, async_client: AsyncClient, test_route: Any
    ) -> None:
        """PATCH /routes/{id} with name/notes updates metadata (no re-route)."""
        response = await async_client.patch(
            f"/routes/{test_route.route_id}",
            json={"name": "Renamed Route", "notes": "updated"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Renamed Route"
        assert data["notes"] == "updated"

    @pytest.mark.asyncio
    async def test_assign_reassign_and_unassign_driver(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_route: Any,
        test_driver: Any,
    ) -> None:
        """Full driver-assignment lifecycle via PATCH driver_id: assign (route
        drops out of the unassigned list), reassign to a different driver, and
        unassign with an explicit null (route returns to the unassigned list)."""
        from app.models.driver import Driver
        from app.models.user import User

        route_id = str(test_route.route_id)

        # Starts unassigned -> appears in the unassigned-only listing.
        unassigned = await async_client.get("/routes?unassigned_only=true")
        assert unassigned.status_code == 200
        assert route_id in {r["route_id"] for r in unassigned.json()["items"]}

        # Assign the driver (with a start time — they travel together).
        assign = await async_client.patch(
            f"/routes/{route_id}",
            json={"driver_id": str(test_driver.driver_id), "start_time": "08:30:00"},
        )
        assert assign.status_code == 200
        assert assign.json()["driver_id"] == str(test_driver.driver_id)
        assert assign.json()["start_time"] == "08:30:00"

        # No longer unassigned.
        unassigned_after = await async_client.get("/routes?unassigned_only=true")
        assert route_id not in {r["route_id"] for r in unassigned_after.json()["items"]}

        # The assigned start_time is surfaced on the list rows (driver homepage).
        listed = await async_client.get("/routes")
        listed_row = next(
            r for r in listed.json()["items"] if r["route_id"] == route_id
        )
        assert listed_row["start_time"] == "08:30:00"

        # Reassign to a second driver.
        other_user = User(
            first_name="Other",
            last_name="Driver",
            email="other-driver@test.dev",
            auth_id="other-drv",
        )
        test_session.add(other_user)
        other_driver = Driver(
            user_id=other_user.user_id,
            phone="+12125550000",
            address="9 Other St",
            license_plate="XYZ789",
            car_make_model="Honda Civic",
        )
        test_session.add(other_driver)
        await test_session.commit()
        await test_session.refresh(other_driver)

        reassign = await async_client.patch(
            f"/routes/{route_id}", json={"driver_id": str(other_driver.driver_id)}
        )
        assert reassign.status_code == 200
        assert reassign.json()["driver_id"] == str(other_driver.driver_id)

        # Unassign via explicit null -> driver_id and start_time both cleared,
        # route back in the unassigned listing.
        unassign = await async_client.patch(
            f"/routes/{route_id}", json={"driver_id": None, "start_time": None}
        )
        assert unassign.status_code == 200
        assert unassign.json()["driver_id"] is None
        assert unassign.json()["start_time"] is None

        unassigned_again = await async_client.get("/routes?unassigned_only=true")
        assert route_id in {r["route_id"] for r in unassigned_again.json()["items"]}

    # NOTE: the GET /routes driver_id filter is ownership-scoped (a driver can
    # only see their own routes; admins may scope to any). Because that rule is
    # enforced by an auth dependency, it's exercised end-to-end against the real
    # auth stack in tests/test_auth_integration.py::TestGetRoutesDriverScoping
    # rather than here (this module bypasses auth).

    @pytest.mark.asyncio
    async def test_update_route_not_found(self, async_client: AsyncClient) -> None:
        """PATCH /routes/{id} returns 404 for an unknown route."""
        response = await async_client.patch(f"/routes/{uuid4()}", json={"name": "x"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_route_invalid_location_ids(
        self, async_client: AsyncClient, test_route: Any
    ) -> None:
        """PATCH /routes/{id} with unknown location_ids returns 400."""
        response = await async_client.patch(
            f"/routes/{test_route.route_id}",
            json={"location_ids": [str(uuid4())]},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_route_reroute_without_warehouse_coords(
        self,
        async_client: AsyncClient,
        test_route: Any,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """Re-routing needs warehouse coords; when system settings exist but
        the warehouse coordinates aren't configured, it's a 503."""
        location_id = (
            await async_client.post(
                "/locations/",
                json={
                    **sample_location_data,
                    "location_group_id": str(test_location_group.location_group_id),
                },
            )
        ).json()["location_id"]
        response = await async_client.patch(
            f"/routes/{test_route.route_id}",
            json={"location_ids": [location_id]},
        )
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_google_maps_link_route_not_found(
        self, async_client: AsyncClient
    ) -> None:
        """GET /routes/{id}/google-maps-link returns 404 for an unknown route."""
        response = await async_client.get(f"/routes/{uuid4()}/google-maps-link")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_google_maps_link_no_stops(
        self, async_client: AsyncClient, test_route: Any
    ) -> None:
        """GET /routes/{id}/google-maps-link returns 422 when the route has no
        stops."""
        response = await async_client.get(
            f"/routes/{test_route.route_id}/google-maps-link"
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_google_maps_link_unfrozen_uses_live_data(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_route: Any,
        test_location_group: Any,
    ) -> None:
        """For an upcoming (unfrozen) route the link is built from the live
        Location rows and the live warehouse in SystemSettings."""
        from urllib.parse import quote

        from sqlmodel import select

        from app.models.system_settings import SystemSettings

        # A settings row already exists (autouse fixture); configure its
        # warehouse coordinates rather than inserting a second row.
        settings = (
            (await test_session.execute(select(SystemSettings).limit(1)))
            .scalars()
            .one()
        )
        settings.warehouse_location = "Depot"
        settings.warehouse_latitude = 43.65
        settings.warehouse_longitude = -79.38
        test_session.add(settings)
        loc = Location(
            location_group_id=test_location_group.location_group_id,
            name="Live Fam",
            contact_name="Live Fam",
            address="10 Live Ave",
            phone_primary="5550001111",
            delivery_type="Family",
            latitude=44.0,
            longitude=-79.0,
        )
        test_session.add(loc)
        await test_session.commit()
        await test_session.refresh(loc)
        test_session.add(
            RouteStop(
                route_id=test_route.route_id,
                location_id=loc.location_id,
                stop_number=1,
            )
        )
        await test_session.commit()

        response = await async_client.get(
            f"/routes/{test_route.route_id}/google-maps-link"
        )
        assert response.status_code == 200
        url = response.json()
        # Origin is the live warehouse; stop is the live address.
        assert "/dir/43.65,-79.38/" in url
        assert quote("10 Live Ave", safe="") in url

    @pytest.mark.asyncio
    async def test_google_maps_link_frozen_uses_snapshot(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_route: Any,
        test_location_group: Any,
    ) -> None:
        """For a frozen route (RouteSnapshot present) the link reflects the
        snapshotted address/coords and the frozen warehouse origin — even after
        the live Location and warehouse have since been mutated."""
        from urllib.parse import quote

        from sqlmodel import select

        from app.models.route_snapshot import RouteSnapshot
        from app.models.system_settings import SystemSettings

        # Live warehouse and location as they are TODAY (post-delivery drift).
        settings = (
            (await test_session.execute(select(SystemSettings).limit(1)))
            .scalars()
            .one()
        )
        settings.warehouse_location = "New Depot"
        settings.warehouse_latitude = 1.0
        settings.warehouse_longitude = 1.0
        test_session.add(settings)
        loc = Location(
            location_group_id=test_location_group.location_group_id,
            name="Moved Fam",
            contact_name="Moved Fam",
            address="999 New Address",
            phone_primary="5550002222",
            delivery_type="Family",
            latitude=2.0,
            longitude=2.0,
        )
        test_session.add(loc)
        await test_session.commit()
        await test_session.refresh(loc)

        stop = RouteStop(
            route_id=test_route.route_id,
            location_id=loc.location_id,
            stop_number=1,
        )
        test_session.add(stop)
        await test_session.commit()
        await test_session.refresh(stop)

        # Freeze: warehouse origin and the delivered address/coords as they
        # were at drive time.
        test_session.add_all(
            [
                RouteSnapshot(
                    route_id=test_route.route_id,
                    start_address="Old Depot",
                    start_latitude=43.65,
                    start_longitude=-79.38,
                ),
                RouteStopSnapshot(
                    route_stop_id=stop.route_stop_id,
                    address="123 Old Address",
                    contact_name="Old Fam",
                    phone_primary="5550002222",
                    num_children=3,
                    notes="",
                    latitude=44.0,
                    longitude=-79.0,
                ),
            ]
        )
        await test_session.commit()

        response = await async_client.get(
            f"/routes/{test_route.route_id}/google-maps-link"
        )
        assert response.status_code == 200
        url = response.json()
        # Origin is the frozen warehouse, not the live (1.0, 1.0).
        assert "/dir/43.65,-79.38/" in url
        assert "/dir/1.0,1.0/" not in url
        # Stop reflects the snapshotted address, not the live one.
        assert quote("123 Old Address", safe="") in url
        assert quote("999 New Address", safe="") not in url

    @pytest.mark.asyncio
    async def test_google_maps_link_frozen_stop_without_snapshot_falls_back(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_route: Any,
        test_location_group: Any,
    ) -> None:
        """A frozen route whose stop lacks a per-stop snapshot (e.g. the freeze
        job skipped it for missing coords) falls back to the live Location for
        that stop, while still using the RouteSnapshot origin."""
        from urllib.parse import quote

        from app.models.route_snapshot import RouteSnapshot

        loc = Location(
            location_group_id=test_location_group.location_group_id,
            name="Unsnapped Fam",
            contact_name="Unsnapped Fam",
            address="55 Fallback Rd",
            phone_primary="5550003333",
            delivery_type="Family",
            latitude=45.0,
            longitude=-80.0,
        )
        test_session.add(loc)
        await test_session.commit()
        await test_session.refresh(loc)

        test_session.add_all(
            [
                RouteStop(
                    route_id=test_route.route_id,
                    location_id=loc.location_id,
                    stop_number=1,
                ),
                RouteSnapshot(
                    route_id=test_route.route_id,
                    start_address="Depot",
                    start_latitude=43.65,
                    start_longitude=-79.38,
                ),
            ]
        )
        await test_session.commit()

        response = await async_client.get(
            f"/routes/{test_route.route_id}/google-maps-link"
        )
        assert response.status_code == 200
        url = response.json()
        assert "/dir/43.65,-79.38/" in url
        assert quote("55 Fallback Rd", safe="") in url

    @pytest.mark.asyncio
    async def test_suggested_driver_by_past_deliveries(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_route_group: Any,
        test_location_group: Any,
    ) -> None:
        """GET /routes/{id}/suggested-driver returns the active driver most
        familiar with the route's locations from past frozen deliveries."""
        from datetime import datetime

        from app.models.driver import Driver
        from app.models.route import Route
        from app.models.route_group import RouteGroup
        from app.models.route_snapshot import RouteSnapshot
        from app.models.user import User

        group_id = test_location_group.location_group_id

        loc_a = Location(
            location_group_id=group_id,
            name="Fam A",
            contact_name="Fam A",
            address="1 A St",
            phone_primary="5550000001",
            delivery_type="Family",
        )
        loc_b = Location(
            location_group_id=group_id,
            name="Fam B",
            contact_name="Fam B",
            address="2 B St",
            phone_primary="5550000002",
            delivery_type="Family",
        )
        user = User(
            first_name="Veteran",
            last_name="Driver",
            email="veteran@test.dev",
            auth_id="veteran-uid",
        )
        driver = Driver(
            user_id=user.user_id,
            phone="+12125551111",
            address="1 Depot Rd",
            license_plate="VET1",
            car_make_model="Toyota Corolla",
            active=True,
        )
        # The driver's past route lives in its own (earlier) group, so the
        # no-double-book exclusion doesn't remove them from the target group.
        past_group = RouteGroup(name="Past Day", drive_date=datetime(2020, 1, 1))
        test_session.add_all([loc_a, loc_b, user, driver, past_group])
        await test_session.commit()
        await test_session.refresh(loc_a)
        await test_session.refresh(loc_b)
        await test_session.refresh(driver)
        await test_session.refresh(past_group)

        # Past route driven by the driver, frozen (RouteSnapshot present),
        # visiting both locations.
        past = Route(
            name="Past",
            length=5.0,
            route_group_id=past_group.route_group_id,
            driver_id=driver.driver_id,
        )
        test_session.add(past)
        await test_session.commit()
        await test_session.refresh(past)
        test_session.add_all(
            [
                RouteStop(
                    route_id=past.route_id,
                    location_id=loc_a.location_id,
                    stop_number=1,
                ),
                RouteStop(
                    route_id=past.route_id,
                    location_id=loc_b.location_id,
                    stop_number=2,
                ),
                RouteSnapshot(
                    route_id=past.route_id,
                    start_address="Warehouse",
                    start_latitude=0.0,
                    start_longitude=0.0,
                ),
            ]
        )
        await test_session.commit()

        # Target route (in the fixture group) visiting location A.
        target = Route(
            name="Target",
            length=3.0,
            route_group_id=test_route_group.route_group_id,
        )
        test_session.add(target)
        await test_session.commit()
        await test_session.refresh(target)
        test_session.add(
            RouteStop(
                route_id=target.route_id, location_id=loc_a.location_id, stop_number=1
            )
        )
        await test_session.commit()

        resp = await async_client.get(
            f"/routes/{target.route_id}/suggested-driver",
            params={"route_group_id": str(test_route_group.route_group_id)},
        )
        assert resp.status_code == 200
        suggestion = resp.json()
        assert suggestion is not None
        assert suggestion["driver_id"] == str(driver.driver_id)
        assert suggestion["driver_name"] == "Veteran Driver"


class TestRouteStopConstraints:
    """DB-level uniqueness guards on route_stops."""

    @staticmethod
    def _make_location(test_location_group: Any, n: int) -> Location:
        return Location(
            location_group_id=test_location_group.location_group_id,
            name=f"Constraint Family {n}",
            contact_name=f"Constraint Family {n}",
            address=f"{n} Constraint St",
            phone_primary=f"555000{n:04d}",
            delivery_type="Family",
            in_roster=True,
        )

    @pytest.mark.asyncio
    async def test_duplicate_stop_number_rejected(
        self,
        test_session: AsyncSession,
        test_route: Any,
        test_location_group: Any,
    ) -> None:
        """Two stops with the same stop_number on one route violate
        UNIQUE(route_id, stop_number)."""
        from sqlalchemy.exc import IntegrityError

        loc_a = self._make_location(test_location_group, 1)
        loc_b = self._make_location(test_location_group, 2)
        test_session.add_all([loc_a, loc_b])
        await test_session.flush()

        test_session.add(
            RouteStop(
                route_id=test_route.route_id,
                location_id=loc_a.location_id,
                stop_number=1,
            )
        )
        await test_session.flush()

        test_session.add(
            RouteStop(
                route_id=test_route.route_id,
                location_id=loc_b.location_id,
                stop_number=1,  # duplicate position on the same route
            )
        )
        with pytest.raises(IntegrityError):
            await test_session.flush()
        await test_session.rollback()

    @pytest.mark.asyncio
    async def test_duplicate_location_rejected(
        self,
        test_session: AsyncSession,
        test_route: Any,
        test_location_group: Any,
    ) -> None:
        """The same location twice on one route violates
        UNIQUE(route_id, location_id) — a family can't be double-delivered
        within a single route."""
        from sqlalchemy.exc import IntegrityError

        loc = self._make_location(test_location_group, 3)
        test_session.add(loc)
        await test_session.flush()

        test_session.add(
            RouteStop(
                route_id=test_route.route_id,
                location_id=loc.location_id,
                stop_number=1,
            )
        )
        await test_session.flush()

        test_session.add(
            RouteStop(
                route_id=test_route.route_id,
                location_id=loc.location_id,  # same family again
                stop_number=2,
            )
        )
        with pytest.raises(IntegrityError):
            await test_session.flush()
        await test_session.rollback()


class TestRouteGroupRoutes:
    """Test suite for route group API routes."""

    @pytest.mark.asyncio
    async def test_get_route_groups_empty(self, async_client: AsyncClient) -> None:
        """Test GET /route-groups returns empty list when no route groups exist."""
        response = await async_client.get("/route-groups")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_create_route_group(
        self, async_client: AsyncClient, sample_route_group_data: dict[str, Any]
    ) -> None:
        """Test POST /route-groups creates a new route group."""
        # Convert datetime to ISO format string
        data = sample_route_group_data.copy()
        data["drive_date"] = data["drive_date"].isoformat()

        response = await async_client.post("/route-groups", json=data)
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == sample_route_group_data["name"]
        assert "route_group_id" in result

    @pytest.mark.asyncio
    async def test_get_route_groups_with_data(
        self, async_client: AsyncClient, test_route_group: Any
    ) -> None:
        """Test GET /route-groups returns list of route groups."""
        response = await async_client.get("/route-groups")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(
            str(rg["route_group_id"]) == str(test_route_group.route_group_id)
            for rg in data
        )

    @pytest.mark.asyncio
    async def test_update_route_group(
        self, async_client: AsyncClient, test_route_group: Any
    ) -> None:
        """Test PATCH /route-groups/{route_group_id} updates a route group."""
        update_data = {"notes": "Updated notes for route group"}
        response = await async_client.patch(
            f"/route-groups/{test_route_group.route_group_id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes for route group"

    @pytest.mark.asyncio
    async def test_update_route_group_not_found(
        self, async_client: AsyncClient
    ) -> None:
        """Test PATCH /route-groups/{route_group_id} returns 404 for non-existent route group."""
        fake_id = uuid4()
        update_data = {"notes": "Updated notes"}
        response = await async_client.patch(
            f"/route-groups/{fake_id}", json=update_data
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_duplicate_route_group_copies_routes_and_stops(
        self, async_client: AsyncClient, test_session: AsyncSession, test_driver: Any
    ) -> None:
        """POST /route-groups/{id}/duplicate creates a copied group with route lineage."""
        from sqlalchemy.orm import selectinload
        from sqlmodel import select

        loc_group = LocationGroup(name="Duplicate Locations", color="#123456", notes="")
        test_session.add(loc_group)
        await test_session.flush()

        loc_a = Location(
            location_group_id=loc_group.location_group_id,
            name="Location A",
            delivery_type="Family",
            contact_name="A",
            address="1 Main St",
            phone_primary="555-0001",
            num_children=2,
        )
        loc_b = Location(
            location_group_id=loc_group.location_group_id,
            name="Location B",
            delivery_type="Family",
            contact_name="B",
            address="2 Main St",
            phone_primary="555-0002",
            num_children=4,
        )
        test_session.add_all([loc_a, loc_b])

        route_group = RouteGroup(
            name="July 9 - Tuesday A",
            notes="original notes",
            drive_date=datetime(2026, 7, 9, 9, 0),
        )
        test_session.add(route_group)
        await test_session.flush()

        route_a = Route(
            name="Route A",
            notes="route notes",
            length=12.5,
            encoded_polyline="abc123",
            ends_at_warehouse=True,
            route_group_id=route_group.route_group_id,
            driver_id=test_driver.driver_id,
        )
        route_b = Route(
            name="Route B",
            notes="second route notes",
            length=3.5,
            route_group_id=route_group.route_group_id,
        )
        test_session.add_all([route_a, route_b])
        await test_session.flush()

        test_session.add_all(
            [
                RouteStop(
                    route_id=route_a.route_id,
                    location_id=loc_a.location_id,
                    stop_number=1,
                ),
                RouteStop(
                    route_id=route_a.route_id,
                    location_id=loc_b.location_id,
                    stop_number=2,
                ),
                RouteStop(
                    route_id=route_b.route_id,
                    location_id=loc_b.location_id,
                    stop_number=1,
                ),
                RouteSnapshot(
                    route_id=route_a.route_id,
                    start_address="Original Warehouse",
                    start_latitude=43.0,
                    start_longitude=-80.0,
                ),
            ]
        )
        await test_session.commit()

        response = await async_client.post(
            f"/route-groups/{route_group.route_group_id}/duplicate"
        )

        assert response.status_code == 201
        body = response.json()
        assert body["route_group_id"] != str(route_group.route_group_id)
        assert body["name"] == "Copy of July 9 - Tuesday A"
        assert body["notes"] == "original notes"
        assert body["num_routes"] == 2
        # Aggregate stats reflect the copied content: 2 distinct locations
        # (loc_b appears on both routes but counts once), boxes derived from
        # num_children (2 + 4 children at the default 2 children/box = 3
        # boxes), and route_a's driver carried over.
        assert body["num_locations"] == 2
        assert body["num_boxes"] == 3
        assert body["num_drivers_assigned"] == 1
        assert body["delivery_type"] == "Family"

        duplicated_group_id = body["route_group_id"]
        result = await test_session.execute(
            select(Route)
            .where(Route.route_group_id == UUID(duplicated_group_id))
            .options(selectinload(Route.route_stops))  # type: ignore[arg-type]
            .order_by(Route.name)
        )
        duplicated_routes = list(result.scalars().all())
        duplicated_route_a, duplicated_route_b = duplicated_routes
        assert duplicated_route_a.route_id != route_a.route_id
        assert duplicated_route_a.name == "Route A"
        assert duplicated_route_a.notes == "route notes"
        assert duplicated_route_a.length == 12.5
        assert duplicated_route_a.encoded_polyline == "abc123"
        assert duplicated_route_a.ends_at_warehouse is True
        assert duplicated_route_a.driver_id == test_driver.driver_id
        assert duplicated_route_a.cloned_from_route_id == route_a.route_id
        assert duplicated_route_a.note_chain_id is None
        assert (
            await test_session.get(RouteSnapshot, duplicated_route_a.route_id) is None
        )
        assert [
            (stop.location_id, stop.stop_number)
            for stop in sorted(
                duplicated_route_a.route_stops, key=lambda item: item.stop_number
            )
        ] == [(loc_a.location_id, 1), (loc_b.location_id, 2)]

        assert duplicated_route_b.route_id != route_b.route_id
        assert duplicated_route_b.name == "Route B"
        assert duplicated_route_b.notes == "second route notes"
        assert duplicated_route_b.length == 3.5
        assert duplicated_route_b.driver_id is None
        assert duplicated_route_b.cloned_from_route_id == route_b.route_id
        assert [
            (stop.location_id, stop.stop_number)
            for stop in duplicated_route_b.route_stops
        ] == [(loc_b.location_id, 1)]

        # PATCH on a group with content returns the same populated aggregates.
        patch_response = await async_client.patch(
            f"/route-groups/{duplicated_group_id}",
            json={"notes": "updated copy notes"},
        )
        assert patch_response.status_code == 200
        patch_body = patch_response.json()
        assert patch_body["notes"] == "updated copy notes"
        assert patch_body["num_routes"] == 2
        assert patch_body["num_locations"] == 2
        assert patch_body["num_boxes"] == 3
        assert patch_body["num_drivers_assigned"] == 1
        assert patch_body["delivery_type"] == "Family"

    @pytest.mark.asyncio
    async def test_duplicate_empty_route_group_truncates_copy_name(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """An empty route group can be duplicated and the copied name stays valid."""
        long_name = "A" * 255
        route_group = RouteGroup(
            name=long_name,
            notes="empty group",
            drive_date=datetime(2026, 7, 10, 9, 0),
        )
        test_session.add(route_group)
        await test_session.commit()

        response = await async_client.post(
            f"/route-groups/{route_group.route_group_id}/duplicate"
        )

        assert response.status_code == 201
        body = response.json()
        assert body["route_group_id"] != str(route_group.route_group_id)
        assert body["name"] == f"Copy of {long_name}"[:255]
        assert len(body["name"]) == 255
        assert body["num_routes"] == 0

    @pytest.mark.asyncio
    async def test_duplicate_route_group_not_found(
        self, async_client: AsyncClient
    ) -> None:
        """POST /route-groups/{id}/duplicate returns 404 for a missing group."""
        response = await async_client.post(f"/route-groups/{uuid4()}/duplicate")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_route_group(
        self,
        async_client: AsyncClient,
        test_route_group: Any,
        test_session: AsyncSession,
    ) -> None:
        """DELETE removes the route group and cascades routes, stops, and snapshots."""
        loc_group = LocationGroup(
            name="Delete Cascade Locations", color="#654321", notes=""
        )
        test_session.add(loc_group)
        await test_session.flush()

        location = Location(
            location_group_id=loc_group.location_group_id,
            name="Delete Cascade Location",
            delivery_type="Family",
            contact_name="Delete",
            address="3 Main St",
            phone_primary="555-0003",
            num_children=2,
        )
        test_session.add(location)
        await test_session.flush()

        route = Route(
            name="Delete Cascade Route",
            length=5.0,
            route_group_id=test_route_group.route_group_id,
        )
        test_session.add(route)
        await test_session.flush()

        route_stop = RouteStop(
            route_id=route.route_id,
            location_id=location.location_id,
            stop_number=1,
        )
        test_session.add(route_stop)
        await test_session.flush()

        test_session.add_all(
            [
                RouteSnapshot(
                    route_id=route.route_id,
                    start_address="Warehouse",
                    start_latitude=43.0,
                    start_longitude=-80.0,
                ),
                RouteStopSnapshot(
                    route_stop_id=route_stop.route_stop_id,
                    address="Snapshot Address",
                    contact_name="Snapshot Contact",
                    phone_primary="555-0100",
                    num_children=2,
                    latitude=43.1,
                    longitude=-80.1,
                ),
            ]
        )
        await test_session.commit()

        response = await async_client.delete(
            f"/route-groups/{test_route_group.route_group_id}"
        )
        assert response.status_code == 204

        # Verify deletion by trying to get all route groups
        get_response = await async_client.get("/route-groups")
        assert response.status_code == 204
        data = get_response.json()
        assert not any(
            str(rg["route_group_id"]) == str(test_route_group.route_group_id)
            for rg in data
        )
        assert await test_session.get(Route, route.route_id) is None
        assert await test_session.get(RouteStop, route_stop.route_stop_id) is None
        assert await test_session.get(RouteSnapshot, route.route_id) is None
        assert (
            await test_session.get(RouteStopSnapshot, route_stop.route_stop_id) is None
        )

    @pytest.mark.asyncio
    async def test_get_route_groups_with_date_filter(
        self,
        async_client: AsyncClient,
        test_route_group: Any,  # noqa: ARG002
    ) -> None:
        """Test GET /route-groups with date filters."""
        start_date = datetime(2024, 1, 1).isoformat()
        end_date = datetime(2024, 12, 31).isoformat()

        response = await async_client.get(
            f"/route-groups?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_route_groups_include_routes(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """GET /route-groups?include_routes=true returns each group's routes.

        Confirms the routes relationship loads without an async lazy-load 500
        and the routes payload is correctly populated.
        """
        rg = RouteGroup(name="RG", drive_date=datetime(2026, 6, 1))
        test_session.add(rg)
        await test_session.commit()
        await test_session.refresh(rg)

        # Route FKs to RouteGroup via route_group_id.
        route = Route(name="R1", length=5.0, route_group_id=rg.route_group_id)
        test_session.add(route)
        await test_session.commit()
        await test_session.refresh(route)

        response = await async_client.get("/route-groups?include_routes=true")
        assert response.status_code == 200
        group = next(
            g for g in response.json() if g["route_group_id"] == str(rg.route_group_id)
        )
        assert group["num_routes"] == 1
        assert [r["route_id"] for r in group["routes"]] == [str(route.route_id)]

    @pytest.mark.asyncio
    async def test_get_route_groups_aggregate_defaults(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """A route group with no memberships returns zeroed aggregates and expected status."""
        rg = RouteGroup(name="Empty Group", drive_date=datetime(2020, 1, 1))
        test_session.add(rg)
        await test_session.commit()
        await test_session.refresh(rg)

        response = await async_client.get("/route-groups")
        assert response.status_code == 200
        group = next(
            g for g in response.json() if g["route_group_id"] == str(rg.route_group_id)
        )
        assert group["num_locations"] == 0
        assert group["num_boxes"] == 0
        assert group["num_drivers_assigned"] == 0
        assert group["delivery_type"] is None
        assert group["status"] == "Completed"

    @pytest.mark.asyncio
    async def test_get_route_groups_delivery_type_school_year(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """A route group with school-linked stops returns delivery_type='School Year'."""
        loc_group = LocationGroup(name="Schools", color="#000000", notes="")
        test_session.add(loc_group)
        await test_session.flush()

        location = Location(
            location_group_id=loc_group.location_group_id,
            name="Central Elementary",
            delivery_type="School",
            contact_name="Jane",
            address="123 Main St",
            phone_primary="555-1234",
            num_children=10,
        )
        test_session.add(location)

        rg = RouteGroup(name="School Group", drive_date=datetime(2020, 3, 1))
        test_session.add(rg)
        await test_session.flush()

        route = Route(name="R1", length=5.0, route_group_id=rg.route_group_id)
        test_session.add(route)
        await test_session.flush()

        test_session.add(
            RouteStop(
                route_id=route.route_id, location_id=location.location_id, stop_number=1
            )
        )
        await test_session.commit()

        response = await async_client.get("/route-groups")
        assert response.status_code == 200
        group = next(
            g for g in response.json() if g["route_group_id"] == str(rg.route_group_id)
        )
        assert group["delivery_type"] == "School"
        assert group["num_locations"] == 1

    @pytest.mark.asyncio
    async def test_get_route_groups_uses_location_delivery_type(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """Route group delivery type comes from its locations without hardcoded types."""
        loc_group = LocationGroup(name="Pantry Group", color="#000000", notes="")
        test_session.add(loc_group)
        await test_session.flush()

        location = Location(
            location_group_id=loc_group.location_group_id,
            name="Pantry Stop",
            delivery_type="Pantry",
            contact_name="Pantry Contact",
            address="123 Main St",
            phone_primary="555-1234",
            num_children=10,
        )
        test_session.add(location)

        rg = RouteGroup(name="Pantry Route Group", drive_date=datetime(2020, 3, 1))
        test_session.add(rg)
        await test_session.flush()

        route = Route(name="R1", length=5.0, route_group_id=rg.route_group_id)
        test_session.add(route)
        await test_session.flush()

        test_session.add(
            RouteStop(
                route_id=route.route_id,
                location_id=location.location_id,
                stop_number=1,
            )
        )
        await test_session.commit()

        response = await async_client.get("/route-groups")
        assert response.status_code == 200
        group = next(
            g for g in response.json() if g["route_group_id"] == str(rg.route_group_id)
        )
        assert group["delivery_type"] == "Pantry"

    @pytest.mark.asyncio
    async def test_get_route_groups_rejects_unknown_delivery_type_filter(
        self, async_client: AsyncClient
    ) -> None:
        """GET /route-groups validates delivery_type filters against settings."""
        response = await async_client.get(
            "/route-groups", params={"delivery_type": "Unknown"}
        )

        assert response.status_code == 422
        assert "Unknown delivery_type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_route_groups_num_boxes_arithmetic(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """num_boxes = sum(ceil(num_children / 2)) per location.
        3 children -> ceil(1.5) = 2, 5 children -> ceil(2.5) = 3, total = 5."""
        loc_group = LocationGroup(name="Boxes Test", color="#111111", notes="")
        test_session.add(loc_group)
        await test_session.flush()

        loc_a = Location(
            location_group_id=loc_group.location_group_id,
            name="Location A",
            delivery_type="Family",
            contact_name="A",
            address="1 St",
            phone_primary="555-0001",
            num_children=3,
        )
        loc_b = Location(
            location_group_id=loc_group.location_group_id,
            name="Location B",
            delivery_type="Family",
            contact_name="B",
            address="2 St",
            phone_primary="555-0002",
            num_children=5,
        )
        test_session.add_all([loc_a, loc_b])

        rg = RouteGroup(name="Boxes Group", drive_date=datetime(2020, 4, 1))
        test_session.add(rg)
        await test_session.flush()

        route = Route(name="R1", length=10.0, route_group_id=rg.route_group_id)
        test_session.add(route)
        await test_session.flush()

        test_session.add(
            RouteStop(
                route_id=route.route_id, location_id=loc_a.location_id, stop_number=1
            )
        )
        test_session.add(
            RouteStop(
                route_id=route.route_id, location_id=loc_b.location_id, stop_number=2
            )
        )
        await test_session.commit()

        response = await async_client.get("/route-groups")
        assert response.status_code == 200
        group = next(
            g for g in response.json() if g["route_group_id"] == str(rg.route_group_id)
        )
        # ceil(3/2) + ceil(5/2) = 2 + 3 = 5
        assert group["num_boxes"] == 5
        assert group["num_locations"] == 2

    @pytest.mark.asyncio
    async def test_get_route_groups_status_today_is_upcoming(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """A route group whose drive_date is today reports status 'Upcoming'.

        drive_date is stored date-only (midnight) and is computed here in the
        scheduler timezone to match the service's clock.
        """
        from zoneinfo import ZoneInfo

        from app.config import settings

        tz = ZoneInfo(settings.scheduler_timezone)
        today = datetime.now(tz).replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=None
        )

        rg = RouteGroup(name="Today Group", drive_date=today)
        test_session.add(rg)
        await test_session.flush()

        route = Route(name="Today R1", length=5.0, route_group_id=rg.route_group_id)
        test_session.add(route)
        await test_session.commit()

        response = await async_client.get("/route-groups")
        assert response.status_code == 200
        group = next(
            g for g in response.json() if g["route_group_id"] == str(rg.route_group_id)
        )
        assert group["status"] == "Upcoming"


class TestNoteChainRoutes:
    """Test suite for note chain API routes."""

    @staticmethod
    async def _create_chain(session: Any) -> str:
        """Helper: create a NoteChain directly in DB, return its ID as string."""
        from app.models.note_chain import NoteChain

        chain = NoteChain(read_permission="All", write_permission="All")
        session.add(chain)
        await session.commit()
        await session.refresh(chain)
        return str(chain.note_chain_id)

    @pytest.mark.asyncio
    async def test_notes_crud_and_read_tracking(
        self, authed_async_client: AsyncClient, test_session: Any
    ) -> None:
        """Test note create, list, update, delete."""
        chain_id = await self._create_chain(test_session)

        # Create
        note_resp = await authed_async_client.post(
            f"/note-chains/{chain_id}/notes",
            json={"message": "Hello"},
        )
        assert note_resp.status_code == 201
        note_id = note_resp.json()["note_id"]

        # List notes
        list_resp = await authed_async_client.get(f"/note-chains/{chain_id}/notes")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 1

        # Update
        patch_resp = await authed_async_client.patch(
            f"/note-chains/{chain_id}/notes/{note_id}",
            json={"message": "Edited"},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["message"] == "Edited"

        # Delete
        delete_note_resp = await authed_async_client.delete(
            f"/note-chains/{chain_id}/notes/{note_id}"
        )
        assert delete_note_resp.status_code == 204

    @pytest.mark.asyncio
    async def test_get_note_chain(
        self, authed_async_client: AsyncClient, test_session: Any
    ) -> None:
        """GET /note-chains/{id} returns the chain for a permitted user."""
        chain_id = await self._create_chain(test_session)
        response = await authed_async_client.get(f"/note-chains/{chain_id}")
        assert response.status_code == 200
        assert response.json()["note_chain_id"] == chain_id

    @pytest.mark.asyncio
    async def test_delete_note_chain(
        self, authed_async_client: AsyncClient, test_session: Any
    ) -> None:
        """DELETE /note-chains/{id} removes the chain (and its notes)."""
        chain_id = await self._create_chain(test_session)
        # Seed a note so the cascade is exercised
        await authed_async_client.post(
            f"/note-chains/{chain_id}/notes", json={"message": "n"}
        )

        response = await authed_async_client.delete(f"/note-chains/{chain_id}")
        assert response.status_code == 204

        get_response = await authed_async_client.get(f"/note-chains/{chain_id}")
        assert get_response.status_code == 404


class TestNoteFeedRoutes:
    """Test suite for cross-location note feed routes."""

    @staticmethod
    async def _seed_location_note(
        session: AsyncSession,
        *,
        location_name: str,
        message: str,
        user: Any = None,
        created_at: datetime,
    ) -> None:
        from app.models.note import Note
        from app.models.note_chain import NoteChain

        group = LocationGroup(name=f"{location_name} Group", color="#000000", notes="")
        chain = NoteChain(read_permission="All", write_permission="All")
        session.add_all([group, chain])
        await session.flush()

        location = Location(
            location_group_id=group.location_group_id,
            name=location_name,
            contact_name=location_name,
            address=f"{location_name} Address",
            phone_primary="555-1234",
            delivery_type="Family",
            note_chain_id=chain.note_chain_id,
        )
        note = Note(
            note_chain_id=chain.note_chain_id,
            user_id=user.user_id if user is not None else None,
            message=message,
            is_system=user is None,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add_all([location, note])
        await session.commit()

    @pytest.mark.asyncio
    async def test_get_notes_feed_recent_page_size(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_admin_user: Any,
    ) -> None:
        await self._seed_location_note(
            test_session,
            location_name="Beta Family",
            message="Older note",
            user=test_admin_user,
            created_at=datetime(2026, 1, 1, 9, 0),
        )
        await self._seed_location_note(
            test_session,
            location_name="Alpha Family",
            message="Newer note",
            user=test_admin_user,
            created_at=datetime(2026, 1, 2, 9, 0),
        )

        response = await async_client.get("/notes?page_size=1&sort=recent")

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        assert body["page"] == 1
        assert body["page_size"] == 1
        assert [item["message"] for item in body["items"]] == ["Newer note"]
        assert body["items"][0]["location_name"] == "Alpha Family"
        assert body["items"][0]["author_name"] == "Admin User"

    @pytest.mark.asyncio
    async def test_get_notes_feed_rejects_invalid_sort(
        self, async_client: AsyncClient
    ) -> None:
        response = await async_client.get("/notes?sort=not-a-sort")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_notes_feed_authorless_note_has_null_author_name(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
    ) -> None:
        # System notes have no author (user_id is None). The feed's outer join
        # to User must surface author_name as null, not " " (Postgres concat
        # coerces NULL args to empty strings, so it must be guarded explicitly).
        await self._seed_location_note(
            test_session,
            location_name="System Family",
            message="Automated note",
            user=None,
            created_at=datetime(2026, 1, 1, 9, 0),
        )

        response = await async_client.get("/notes?sort=recent")

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        item = body["items"][0]
        assert item["message"] == "Automated note"
        assert item["author_name"] is None
        assert item["author_role"] is None

    @pytest.mark.asyncio
    async def test_get_notes_feed_supports_sorting_and_pagination(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        test_admin_user: Any,
    ) -> None:
        from app.models.user import User

        driver_user = User(
            first_name="Zara",
            last_name="Driver",
            email="zara.driver@example.com",
            auth_id=None,
            role="driver",
        )
        test_session.add(driver_user)
        await test_session.commit()
        await test_session.refresh(driver_user)

        await self._seed_location_note(
            test_session,
            location_name="Charlie Location",
            message="Admin middle",
            user=test_admin_user,
            created_at=datetime(2026, 1, 2, 9, 0),
        )
        await self._seed_location_note(
            test_session,
            location_name="Alpha Location",
            message="Driver newest",
            user=driver_user,
            created_at=datetime(2026, 1, 3, 9, 0),
        )
        await self._seed_location_note(
            test_session,
            location_name="Bravo Location",
            message="Admin oldest",
            user=test_admin_user,
            created_at=datetime(2026, 1, 1, 9, 0),
        )

        oldest_response = await async_client.get("/notes?sort=oldest")
        location_response = await async_client.get("/notes?sort=location")
        driver_response = await async_client.get("/notes?sort=driver")
        page_response = await async_client.get("/notes?page=2&page_size=1&sort=recent")

        assert oldest_response.status_code == 200
        assert [item["message"] for item in oldest_response.json()["items"]] == [
            "Admin oldest",
            "Admin middle",
            "Driver newest",
        ]

        assert location_response.status_code == 200
        assert [
            item["location_name"] for item in location_response.json()["items"]
        ] == [
            "Alpha Location",
            "Bravo Location",
            "Charlie Location",
        ]

        assert driver_response.status_code == 200
        assert [item["author_name"] for item in driver_response.json()["items"]] == [
            "Zara Driver",
            "Admin User",
            "Admin User",
        ]

        assert page_response.status_code == 200
        page_body = page_response.json()
        assert page_body["total"] == 3
        assert page_body["page"] == 2
        assert page_body["page_size"] == 1
        assert page_body["items"][0]["message"] == "Admin middle"


class TestValidationErrors:
    """Test suite for validation error handling across routes."""

    @pytest.mark.asyncio
    async def test_create_driver_invalid_phone(self, async_client: AsyncClient) -> None:
        """Test POST /drivers with invalid phone number returns validation error."""
        invalid_data = {
            "first_name": "Test",
            "last_name": "Driver",
            "email": "test@example.com",
            "phone": "invalid-phone",  # Invalid phone format
            "address": "123 Main St",
            "license_plate": "ABC123",
            "car_make_model": "Toyota Camry",
        }
        with patch(
            "app.dependencies.auth.auth_service.is_authorized_by_role",
            new_callable=AsyncMock,
            return_value=True,
        ):
            response = await async_client.post(
                "/drivers/initialize",
                json=invalid_data,
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_location_missing_required_fields(
        self, async_client: AsyncClient
    ) -> None:
        """Test POST /locations with missing required fields returns validation error."""
        invalid_data = {
            "contact_name": "Jane Smith",
            # Missing: address, phone_primary, longitude, latitude, halal
        }
        response = await async_client.post("/locations/", json=invalid_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_route_group_invalid_date(
        self, async_client: AsyncClient
    ) -> None:
        """Test POST /route-groups with invalid date format returns validation error."""
        invalid_data = {
            "name": "Test Route Group",
            "notes": "Test notes",
            "drive_date": "not-a-date",  # Invalid date format
        }
        response = await async_client.post("/route-groups", json=invalid_data)
        assert response.status_code == 422


class TestAnnouncementRoutes:
    """Test suite for announcement API routes."""

    @pytest.mark.asyncio
    async def test_get_announcements_empty(
        self, authed_async_client: AsyncClient
    ) -> None:
        """Test GET /announcements returns empty list when none exist."""
        response = await authed_async_client.get("/announcements/")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_create_announcement(
        self,
        authed_async_client: AsyncClient,
        test_admin_user: Any,
        sample_announcement_data: dict[str, Any],
    ) -> None:
        """Test POST /announcements creates a new announcement."""
        response = await authed_async_client.post(
            "/announcements/", json=sample_announcement_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["subject"] == sample_announcement_data["subject"]
        assert data["message"] == sample_announcement_data["message"]
        assert data["user_id"] == str(test_admin_user.user_id)
        assert "announcement_id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_get_announcement_by_id(
        self,
        authed_async_client: AsyncClient,
        sample_announcement_data: dict[str, Any],
    ) -> None:
        """Test GET /announcements/{id} returns the announcement."""
        create_response = await authed_async_client.post(
            "/announcements/", json=sample_announcement_data
        )
        announcement_id = create_response.json()["announcement_id"]

        response = await authed_async_client.get(f"/announcements/{announcement_id}")
        assert response.status_code == 200
        assert response.json()["subject"] == sample_announcement_data["subject"]

    @pytest.mark.asyncio
    async def test_get_announcement_not_found(self, async_client: AsyncClient) -> None:
        """Test GET /announcements/{id} returns 404 for nonexistent ID."""
        fake_id = uuid4()
        response = await async_client.get(f"/announcements/{fake_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_announcement(
        self,
        authed_async_client: AsyncClient,
        sample_announcement_data: dict[str, Any],
    ) -> None:
        """Test PUT /announcements/{id} updates the announcement."""
        create_response = await authed_async_client.post(
            "/announcements/", json=sample_announcement_data
        )
        announcement_id = create_response.json()["announcement_id"]

        update_data = {"subject": "Updated Subject"}
        response = await authed_async_client.put(
            f"/announcements/{announcement_id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["subject"] == "Updated Subject"
        assert data["message"] == sample_announcement_data["message"]
        assert data["updated_at"] is not None
        assert data["updated_at"] != data["created_at"]

    @pytest.mark.asyncio
    async def test_delete_announcement(
        self,
        authed_async_client: AsyncClient,
        sample_announcement_data: dict[str, Any],
    ) -> None:
        """Test DELETE /announcements/{id} removes the announcement."""
        create_response = await authed_async_client.post(
            "/announcements/", json=sample_announcement_data
        )
        announcement_id = create_response.json()["announcement_id"]

        response = await authed_async_client.delete(f"/announcements/{announcement_id}")
        assert response.status_code == 204

        get_response = await authed_async_client.get(
            f"/announcements/{announcement_id}"
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_announcement_not_found(
        self, authed_async_client: AsyncClient
    ) -> None:
        """Test DELETE /announcements/{id} returns 404 for nonexistent ID."""
        fake_id = uuid4()
        response = await authed_async_client.delete(f"/announcements/{fake_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_send_announcement_email(
        self,
        authed_async_client: AsyncClient,
        test_driver: Any,
        sample_announcement_data: dict[str, Any],
        mocker: Any,
    ) -> None:
        """POST /announcements/{id}/email notifies active drivers."""
        mocker.patch(
            "app.services.implementations.email_dispatcher.EmailDispatcher.dispatch",
            new_callable=mocker.AsyncMock,
        )

        create_response = await authed_async_client.post(
            "/announcements/", json=sample_announcement_data
        )
        announcement_id = create_response.json()["announcement_id"]

        response = await authed_async_client.post(
            f"/announcements/{announcement_id}/email"
        )
        assert response.status_code == 200
        assert response.json() == {"sent": 1, "failed": 0}
        assert test_driver.user_id is not None


class TestJobRoutes:
    """Test suite for job API routes."""

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, async_client: AsyncClient) -> None:
        """GET /jobs/{id} returns 404 (not 500) for an unknown job.

        Regression: the 404 HTTPException was raised inside a try whose bare
        `except Exception` swallowed it and rewrapped it as a 500.
        """
        response = await async_client.get(f"/jobs/{uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_job(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """GET /jobs/{id} returns the job."""
        from app.models.job import Job

        job = Job()
        test_session.add(job)
        await test_session.commit()
        await test_session.refresh(job)

        response = await async_client.get(f"/jobs/{job.job_id}")
        assert response.status_code == 200
        assert response.json()["job_id"] == str(job.job_id)

    @pytest.mark.asyncio
    async def test_get_jobs_empty(self, async_client: AsyncClient) -> None:
        """GET /jobs returns an empty list when none exist."""
        response = await async_client.get("/jobs/")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_jobs_with_data(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """GET /jobs returns created jobs."""
        from app.models.job import Job

        job = Job()
        test_session.add(job)
        await test_session.commit()
        await test_session.refresh(job)

        response = await async_client.get("/jobs/")
        assert response.status_code == 200
        ids = [j["job_id"] for j in response.json()]
        assert str(job.job_id) in ids

    @pytest.mark.asyncio
    async def test_generate_job(self, client_with_overrides: Any) -> None:
        """POST /jobs/generate enqueues a job and returns its id (202).

        The job service is faked so the test doesn't kick off real
        route-generation/scheduler work.
        """
        from app.routers.job_routes import get_job_service

        job_id = uuid4()

        class _FakeJobService:
            async def generate_job(self, _req: Any = None) -> Any:
                return job_id

            async def enqueue(self, _job_id: Any) -> None:
                return None

        client = await client_with_overrides({get_job_service: _FakeJobService})
        body = {
            "location_group": {"name": "Group", "color": "#FF5733", "notes": ""},
            "settings": {"route_start_time": "2026-06-01T08:00:00", "num_routes": 2},
        }
        response = await client.post("/jobs/generate", json=body)
        assert response.status_code == 202
        assert response.json()["job_id"] == str(job_id)

    @pytest.mark.asyncio
    async def test_cancel_pending_job(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """POST /jobs/{id}/cancel marks a pending job as cancelled."""
        from app.models.job import Job

        job = Job(progress=ProgressEnum.PENDING)
        test_session.add(job)
        await test_session.commit()

        response = await async_client.post(f"/jobs/{job.job_id}/cancel")

        assert response.status_code == 200
        body = response.json()
        assert body["progress"] == "Cancelled"
        await test_session.refresh(job)
        assert job.progress == ProgressEnum.CANCELLED
        assert job.finished_at is not None

    @pytest.mark.asyncio
    async def test_cancel_running_job_prevents_late_completion(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """A cancelled running job stays cancelled if worker completion arrives later."""
        from app.models.job import Job
        from app.services.implementations.job_service import JobService

        job = Job(progress=ProgressEnum.RUNNING)
        test_session.add(job)
        await test_session.commit()

        response = await async_client.post(f"/jobs/{job.job_id}/cancel")

        assert response.status_code == 200
        assert response.json()["progress"] == "Cancelled"

        service = JobService(logger=MagicMock(), session=test_session)
        await service.update_progress(job.job_id, ProgressEnum.COMPLETED)
        await test_session.refresh(job)
        assert job.progress == ProgressEnum.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_finished_job_is_safe_noop(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        """Cancelling completed/failed work returns the existing terminal state."""
        from app.models.job import Job

        job = Job(progress=ProgressEnum.COMPLETED)
        test_session.add(job)
        await test_session.commit()

        response = await async_client.post(f"/jobs/{job.job_id}/cancel")

        assert response.status_code == 200
        assert response.json()["progress"] == "Completed"
        await test_session.refresh(job)
        assert job.progress == ProgressEnum.COMPLETED

    @pytest.mark.asyncio
    async def test_cancel_job_not_found(self, async_client: AsyncClient) -> None:
        """POST /jobs/{id}/cancel returns 404 for an unknown job."""
        response = await async_client.post(f"/jobs/{uuid4()}/cancel")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_enqueue_cancelled_job_does_not_run(
        self, test_session: AsyncSession
    ) -> None:
        """Queued work checks job state before moving to Running."""
        from app.models.job import Job
        from app.services.implementations.job_service import JobService

        job = Job(progress=ProgressEnum.CANCELLED)
        test_session.add(job)
        await test_session.commit()

        service = JobService(logger=MagicMock(), session=test_session)
        await service.enqueue(job.job_id)

        await test_session.refresh(job)
        assert job.progress == ProgressEnum.CANCELLED


class TestSystemSettingsRoutes:
    """Test suite for system settings API routes."""

    @pytest.mark.asyncio
    async def test_get_system_settings(self, async_client: AsyncClient) -> None:
        """GET /system-settings returns 200 (null-safe when unset)."""
        response = await async_client.get("/system-settings/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_patch_system_settings(self, async_client: AsyncClient) -> None:
        """PATCH /system-settings creates or updates the singleton row."""
        response = await async_client.patch(
            "/system-settings/",
            json={
                "boxes_per_car": 12,
                "contact_phone": "+12125551234",
                "delivery_types": ["School", "Family", "Pantry"],
                "email_reminders": [
                    {"days_before": 1, "time": "09:00:00"},
                    {"days_before": 0, "time": "11:00:00"},
                ],
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["boxes_per_car"] == 12
        assert body["contact_phone"] == "+12125551234"
        assert body["delivery_types"] == ["School", "Family", "Pantry"]
        assert body["email_reminders"] == [
            {"days_before": 1, "time": "09:00:00"},
            {"days_before": 0, "time": "11:00:00"},
        ]

    @pytest.mark.asyncio
    async def test_patch_system_settings_rejects_empty_delivery_types(
        self, async_client: AsyncClient
    ) -> None:
        """PATCH /system-settings rejects unusable delivery type lists."""
        response = await async_client.patch(
            "/system-settings/", json={"delivery_types": ["School", ""]}
        )
        assert response.status_code == 422

    async def _create_location(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        location_group_id: str,
        *,
        delivery_type: str,
        name: str,
        phone_primary: str,
    ) -> str:
        """Create a location and return its id (helper for guard/rename tests)."""
        response = await async_client.post(
            "/locations/",
            json={
                **sample_location_data,
                "location_group_id": location_group_id,
                "name": name,
                "contact_name": name,
                "phone_primary": phone_primary,
                "delivery_type": delivery_type,
            },
        )
        assert response.status_code == 201, response.text
        return str(response.json()["location_id"])

    @pytest.mark.asyncio
    async def test_patch_blocks_removing_delivery_type_in_active_use(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """Removing a delivery type an on-roster location uses is blocked (409)."""
        await self._create_location(
            async_client,
            sample_location_data,
            str(test_location_group.location_group_id),
            delivery_type="School",
            name="Central Elementary",
            phone_primary="(555) 111-1111",
        )

        response = await async_client.patch(
            "/system-settings/", json={"delivery_types": ["Family"]}
        )

        assert response.status_code == 409
        assert "School" in response.json()["detail"]

        # The removal must not have persisted: the stored list still carries it.
        settings = await async_client.get("/system-settings/")
        assert "School" in settings.json()["delivery_types"]

    @pytest.mark.asyncio
    async def test_patch_allows_removing_unused_delivery_type(
        self, async_client: AsyncClient
    ) -> None:
        """A delivery type no location uses can be removed freely."""
        await async_client.patch(
            "/system-settings/",
            json={"delivery_types": ["School", "Family", "Pantry"]},
        )

        response = await async_client.patch(
            "/system-settings/", json={"delivery_types": ["School", "Family"]}
        )

        assert response.status_code == 200
        assert response.json()["delivery_types"] == ["School", "Family"]

    @pytest.mark.asyncio
    async def test_patch_allows_removing_type_used_only_by_inactive_location(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """Off-roster (Inactive) locations don't block removing their type."""
        await async_client.patch(
            "/system-settings/",
            json={"delivery_types": ["School", "Family", "Pantry"]},
        )
        location_id = await self._create_location(
            async_client,
            sample_location_data,
            str(test_location_group.location_group_id),
            delivery_type="Pantry",
            name="Old Pantry",
            phone_primary="(555) 333-3333",
        )
        # Take it off the roster -> Inactive.
        deactivate = await async_client.patch(
            f"/locations/{location_id}", json={"in_roster": False}
        )
        assert deactivate.status_code == 200

        response = await async_client.patch(
            "/system-settings/", json={"delivery_types": ["School", "Family"]}
        )

        assert response.status_code == 200
        assert response.json()["delivery_types"] == ["School", "Family"]

    @pytest.mark.asyncio
    async def test_rename_delivery_type_cascades_to_locations(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """Renaming a type updates the settings list and every location using it."""
        location_id = await self._create_location(
            async_client,
            sample_location_data,
            str(test_location_group.location_group_id),
            delivery_type="School",
            name="Central Elementary",
            phone_primary="(555) 111-1111",
        )

        response = await async_client.post(
            "/system-settings/delivery-types/rename",
            json={"old_name": "School", "new_name": "Elementary"},
        )

        assert response.status_code == 200, response.text
        delivery_types = response.json()["delivery_types"]
        assert "Elementary" in delivery_types
        assert "School" not in delivery_types

        # The location now carries the new name and filters under it.
        location = await async_client.get(f"/locations/{location_id}")
        assert location.json()["delivery_type"] == "Elementary"
        filtered = await async_client.get(
            "/locations/", params={"delivery_type": "Elementary"}
        )
        ids = {loc["location_id"] for loc in filtered.json()["items"]}
        assert location_id in ids

    @pytest.mark.asyncio
    async def test_rename_delivery_type_cascades_to_inactive_locations(
        self,
        async_client: AsyncClient,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """Rename preserves identity, so it follows Inactive locations too."""
        await async_client.patch(
            "/system-settings/",
            json={"delivery_types": ["School", "Family", "Pantry"]},
        )
        location_id = await self._create_location(
            async_client,
            sample_location_data,
            str(test_location_group.location_group_id),
            delivery_type="Pantry",
            name="Old Pantry",
            phone_primary="(555) 333-3333",
        )
        deactivate = await async_client.patch(
            f"/locations/{location_id}", json={"in_roster": False}
        )
        assert deactivate.status_code == 200

        response = await async_client.post(
            "/system-settings/delivery-types/rename",
            json={"old_name": "Pantry", "new_name": "Food Bank"},
        )

        assert response.status_code == 200, response.text
        location = await async_client.get(f"/locations/{location_id}")
        assert location.json()["delivery_type"] == "Food Bank"

    @pytest.mark.asyncio
    async def test_rename_delivery_type_rejects_unknown_source(
        self, async_client: AsyncClient
    ) -> None:
        """Renaming a type that isn't configured fails fast (422)."""
        response = await async_client.post(
            "/system-settings/delivery-types/rename",
            json={"old_name": "Nonexistent", "new_name": "Whatever"},
        )
        assert response.status_code == 422
        assert "Nonexistent" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_rename_delivery_type_rejects_existing_target(
        self, async_client: AsyncClient
    ) -> None:
        """Renaming onto an existing type would merge two types, so it's blocked."""
        response = await async_client.post(
            "/system-settings/delivery-types/rename",
            json={"old_name": "School", "new_name": "Family"},
        )
        assert response.status_code == 422
        assert "already exists" in response.json()["detail"]


class _FakeUploadResult:
    def __init__(self, url: str, filename: str) -> None:
        self.url = url
        self.filename = filename


class _FakeGCP:
    """Stand-in for GCPStorageClient. Constructed with no args so it can be
    passed directly as a dependency override (FastAPI inspects __init__ params);
    set upload_error / delete_error on the instance to simulate failures.
    """

    upload_error: Exception | None = None
    delete_error: Exception | None = None

    def upload_file(self, _contents: bytes, filename: str, _content_type: str) -> Any:
        if self.upload_error:
            raise self.upload_error
        return _FakeUploadResult(url=f"https://gcs.test/{filename}", filename=filename)

    def delete_file(self, _filename: str) -> None:
        if self.delete_error:
            raise self.delete_error


class TestUploadRoutes:
    """Test suite for upload API routes (GCP client stubbed)."""

    @pytest.mark.asyncio
    async def test_upload_image_success(self, client_with_overrides: Any) -> None:
        """POST /upload returns the stored file's url + filename."""
        from app.dependencies.services import get_gcp_storage_client

        client = await client_with_overrides({get_gcp_storage_client: _FakeGCP})
        response = await client.post(
            "/upload/", files={"file": ("pic.png", b"data", "image/png")}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["filename"] == "pic.png"
        assert body["url"].endswith("pic.png")

    @pytest.mark.asyncio
    async def test_upload_rejects_bad_content_type(
        self, client_with_overrides: Any
    ) -> None:
        """POST /upload rejects unsupported content types with 400."""
        from app.dependencies.services import get_gcp_storage_client

        client = await client_with_overrides({get_gcp_storage_client: _FakeGCP})
        response = await client.post(
            "/upload/", files={"file": ("notes.txt", b"data", "text/plain")}
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_rejects_oversize(self, client_with_overrides: Any) -> None:
        """POST /upload rejects files over the size limit with 400."""
        from app.dependencies.services import get_gcp_storage_client

        client = await client_with_overrides({get_gcp_storage_client: _FakeGCP})
        big = b"x" * (5 * 1024 * 1024 + 1)
        response = await client.post(
            "/upload/", files={"file": ("big.png", big, "image/png")}
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_permission_denied_maps_to_403(
        self, client_with_overrides: Any
    ) -> None:
        """A GCS permission error maps to 403."""
        from app.dependencies.services import get_gcp_storage_client
        from app.utilities.gcp_client import GCSStorageError

        fake = _FakeGCP()
        fake.upload_error = GCSStorageError("upload failed: permission denied")
        client = await client_with_overrides({get_gcp_storage_client: lambda: fake})
        response = await client.post(
            "/upload/", files={"file": ("pic.png", b"data", "image/png")}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_upload_storage_error_maps_to_503(
        self, client_with_overrides: Any
    ) -> None:
        """A generic GCS error maps to 503."""
        from app.dependencies.services import get_gcp_storage_client
        from app.utilities.gcp_client import GCSStorageError

        fake = _FakeGCP()
        fake.upload_error = GCSStorageError("bucket unavailable")
        client = await client_with_overrides({get_gcp_storage_client: lambda: fake})
        response = await client.post(
            "/upload/", files={"file": ("pic.png", b"data", "image/png")}
        )
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_delete_image_success(self, client_with_overrides: Any) -> None:
        """DELETE /upload/{filename} succeeds."""
        from app.dependencies.services import get_gcp_storage_client

        client = await client_with_overrides({get_gcp_storage_client: _FakeGCP})
        response = await client.delete("/upload/pic.png")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_image_not_found(self, client_with_overrides: Any) -> None:
        """DELETE /upload/{filename} returns 404 when the file is missing."""
        from app.dependencies.services import get_gcp_storage_client

        fake = _FakeGCP()
        fake.delete_error = FileNotFoundError("missing")
        client = await client_with_overrides({get_gcp_storage_client: lambda: fake})
        response = await client.delete("/upload/missing.png")
        assert response.status_code == 404


class TestDriverHistoryRoutes:
    """Test suite for the driver-history sub-router."""

    @staticmethod
    def _base(test_driver: Any) -> str:
        return f"/drivers/{test_driver.driver_id}/history"

    @pytest.mark.asyncio
    async def test_get_summary(
        self, async_client: AsyncClient, test_driver: Any
    ) -> None:
        """GET /summary returns lifetime + current-year km for the driver."""
        response = await async_client.get(f"{self._base(test_driver)}/summary")
        assert response.status_code == 200
        body = response.json()
        assert "lifetime_km" in body
        assert "current_year_km" in body

    @pytest.mark.asyncio
    async def test_get_summary_driver_not_found(
        self, async_client: AsyncClient
    ) -> None:
        """GET /summary returns 404 for an unknown driver (rather than a
        zero-filled summary)."""
        response = await async_client.get(f"/drivers/{uuid4()}/history/summary")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_driver_history(
        self, async_client: AsyncClient, test_driver: Any
    ) -> None:
        """POST / creates a history entry."""
        response = await async_client.post(
            f"{self._base(test_driver)}/",
            json={"year": 2025, "month": 1, "km": 12.5},
        )
        assert response.status_code == 201
        assert response.json()["km"] == 12.5

    @pytest.mark.asyncio
    async def test_create_driver_history_driver_not_found(
        self, async_client: AsyncClient
    ) -> None:
        """POST / returns 404 when the driver doesn't exist."""
        response = await async_client.post(
            f"/drivers/{uuid4()}/history/",
            json={"year": 2025, "month": 1, "km": 5.0},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_driver_history_conflict(
        self, async_client: AsyncClient, test_driver: Any
    ) -> None:
        """POST / twice for the same (driver, year, month) returns 409."""
        body = {"year": 2025, "month": 2, "km": 3.0}
        first = await async_client.post(f"{self._base(test_driver)}/", json=body)
        assert first.status_code == 201
        second = await async_client.post(f"{self._base(test_driver)}/", json=body)
        assert second.status_code == 409

    @pytest.mark.asyncio
    async def test_list_driver_history(
        self, async_client: AsyncClient, test_driver: Any
    ) -> None:
        """GET / lists the driver's history entries."""
        await async_client.post(
            f"{self._base(test_driver)}/",
            json={"year": 2025, "month": 3, "km": 7.0},
        )
        response = await async_client.get(f"{self._base(test_driver)}/")
        assert response.status_code == 200
        assert any(h["month"] == 3 for h in response.json())

    @pytest.mark.asyncio
    async def test_list_driver_history_month_without_year(
        self, async_client: AsyncClient, test_driver: Any
    ) -> None:
        """GET /?month=... without a year is a 400."""
        response = await async_client.get(f"{self._base(test_driver)}/?month=1")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_update_driver_history(
        self, async_client: AsyncClient, test_driver: Any
    ) -> None:
        """PATCH /?year=&month= updates the km for that entry."""
        await async_client.post(
            f"{self._base(test_driver)}/",
            json={"year": 2025, "month": 4, "km": 1.0},
        )
        response = await async_client.patch(
            f"{self._base(test_driver)}/?year=2025&month=4",
            json={"km": 9.0},
        )
        assert response.status_code == 200
        assert response.json()["km"] == 9.0

    @pytest.mark.asyncio
    async def test_delete_driver_history(
        self, async_client: AsyncClient, test_driver: Any
    ) -> None:
        """DELETE /?year=&month= removes the entry."""
        await async_client.post(
            f"{self._base(test_driver)}/",
            json={"year": 2025, "month": 5, "km": 2.0},
        )
        response = await async_client.delete(
            f"{self._base(test_driver)}/?year=2025&month=5"
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_export_driver_history(
        self, async_client: AsyncClient, test_driver: Any
    ) -> None:
        """GET /drivers/all/history/{year}/export streams a CSV of all drivers'
        history (driver_id must be the literal "all")."""
        await async_client.post(
            f"{self._base(test_driver)}/",
            json={"year": 2025, "month": 6, "km": 4.0},
        )
        response = await async_client.get("/drivers/all/history/2025/export")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        # The CSV emits a per-year distance column, proving the export ran for
        # the requested year.
        assert "distance (km) in 2025" in response.text

    @pytest.mark.asyncio
    async def test_mark_read_and_is_read_status(
        self,
        authed_async_client: AsyncClient,
        test_admin_user: Any,
        sample_announcement_data: dict[str, Any],
    ) -> None:
        """Test POST /announcements/mark-read and is_read on GET /announcements/."""
        user_id = str(test_admin_user.user_id)

        # Create an announcement
        create_resp = await authed_async_client.post(
            "/announcements/", json=sample_announcement_data
        )
        assert create_resp.status_code == 201

        # GET — is_read should be False (never marked read)
        resp = await authed_async_client.get("/announcements/")
        assert resp.status_code == 200
        assert resp.json()[0]["is_read"] is False

        # Mark as read (user derived from auth token)
        mark_resp = await authed_async_client.post("/announcements/mark-read")
        assert mark_resp.status_code == 200
        assert mark_resp.json()["user_id"] == user_id
        assert "last_read_at" in mark_resp.json()
        first_last_read_at = mark_resp.json()["last_read_at"]

        mark_again = await authed_async_client.post("/announcements/mark-read")
        assert mark_again.status_code == 200
        assert mark_again.json()["user_id"] == user_id
        assert mark_again.json()["last_read_at"] >= first_last_read_at

        # GET — is_read should be True now
        resp = await authed_async_client.get("/announcements/")
        assert resp.status_code == 200
        assert resp.json()[0]["is_read"] is True

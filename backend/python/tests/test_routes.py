"""
Comprehensive integration tests for API routes.

Tests cover:
- Driver routes (CRUD operations)
- Location routes (CRUD operations)
- Route routes (read and delete operations)
- Route group routes (CRUD operations)
- Error handling (404s, validation errors)
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enum import DeliveryTypeEnum
from app.models.location import Location
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_stop import RouteStop


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
                "delivery_type": DeliveryTypeEnum.SCHOOL.value,
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
                "delivery_type": DeliveryTypeEnum.FAMILY.value,
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
            delivery_type=DeliveryTypeEnum.FAMILY,
            in_roster=True,
        )
        unscheduled_location = Location(
            location_group_id=test_location_group.location_group_id,
            name="Unscheduled Family",
            contact_name="Unscheduled Family",
            address="2 Unscheduled St",
            phone_primary="5552222222",
            delivery_type=DeliveryTypeEnum.FAMILY,
            in_roster=True,
        )
        inactive_location = Location(
            location_group_id=test_location_group.location_group_id,
            name="Inactive Family",
            contact_name="Inactive Family",
            address="3 Inactive St",
            phone_primary="5553333333",
            delivery_type=DeliveryTypeEnum.FAMILY,
            in_roster=False,
        )
        archived_scheduled_location = Location(
            location_group_id=test_location_group.location_group_id,
            name="Archived Scheduled Family",
            contact_name="Archived Scheduled Family",
            address="4 Archived Scheduled St",
            phone_primary="5554444444",
            delivery_type=DeliveryTypeEnum.FAMILY,
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
            delivery_type=DeliveryTypeEnum.SCHOOL,
            in_roster=True,
        )
        active_family_location = Location(
            location_group_id=test_location_group.location_group_id,
            name="Active Family",
            contact_name="Active Family",
            address="1 Family St",
            phone_primary="5556666666",
            delivery_type=DeliveryTypeEnum.FAMILY,
            in_roster=True,
        )
        unscheduled_school_location = Location(
            location_group_id=test_location_group.location_group_id,
            name="Unscheduled Elementary",
            contact_name="Unscheduled School",
            address="2 School St",
            phone_primary="5557777777",
            delivery_type=DeliveryTypeEnum.SCHOOL,
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
        update_data = {"notes": "Updated notes"}
        response = await async_client.patch(
            f"/locations/{location_id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes"

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
            num_boxes=3,
            delivery_type=DeliveryTypeEnum.FAMILY,
        )
        loc_b = Location(
            location_group_id=test_location_group.location_group_id,
            name="Route Stop B",
            contact_name="Route Stop B",
            address="2 Route St",
            phone_primary="5550000002",
            num_boxes=5,
            delivery_type=DeliveryTypeEnum.FAMILY,
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

    @pytest.mark.asyncio
    async def test_get_route_by_id(
        self, async_client: AsyncClient, test_route: Any
    ) -> None:
        """GET /routes/{id} returns the route."""
        response = await async_client.get(f"/routes/{test_route.route_id}")
        assert response.status_code == 200
        assert response.json()["route_id"] == str(test_route.route_id)

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
        test_session: AsyncSession,
        test_route: Any,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """Re-routing needs warehouse coords; when system settings exist but
        the warehouse coordinates aren't configured, it's a 503."""
        from app.models.system_settings import SystemSettings

        # Settings exist but have no warehouse lat/long.
        test_session.add(SystemSettings())
        await test_session.commit()

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
    async def test_update_route_reroute_without_system_settings(
        self,
        async_client: AsyncClient,
        test_route: Any,
        sample_location_data: dict[str, Any],
        test_location_group: Any,
    ) -> None:
        """Re-routing with no system settings at all is a 503 (server not
        configured), not a 400 — even though the error says 'not found'."""
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
            delivery_type=DeliveryTypeEnum.FAMILY,
        )
        loc_b = Location(
            location_group_id=group_id,
            name="Fam B",
            contact_name="Fam B",
            address="2 B St",
            phone_primary="5550000002",
            delivery_type=DeliveryTypeEnum.FAMILY,
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
            delivery_type=DeliveryTypeEnum.FAMILY,
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
    async def test_delete_route_group(
        self, async_client: AsyncClient, test_route_group: Any
    ) -> None:
        """Test DELETE /route-groups/{route_group_id} deletes a route group."""
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
        from datetime import datetime

        from app.models.route import Route
        from app.models.route_group import RouteGroup

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
        """Test note create, list (with unread count + auto mark-as-read), update, delete."""
        chain_id = await self._create_chain(test_session)

        # Create
        note_resp = await authed_async_client.post(
            f"/note-chains/{chain_id}/notes",
            json={"message": "Hello"},
        )
        assert note_resp.status_code == 201
        note_id = note_resp.json()["note_id"]

        # List - unread_count=1, then auto-marked as read
        list_resp = await authed_async_client.get(f"/note-chains/{chain_id}/notes")
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert len(data["notes"]) == 1
        assert data["unread_count"] == 1

        # List again - unread_count=0
        list_again_resp = await authed_async_client.get(
            f"/note-chains/{chain_id}/notes"
        )
        assert list_again_resp.json()["unread_count"] == 0

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
            # Missing: address, phone_primary, longitude, latitude, halal, num_boxes
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
    async def test_get_announcements_empty(self, async_client: AsyncClient) -> None:
        """Test GET /announcements returns empty list when none exist."""
        response = await async_client.get("/announcements/")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_create_announcement(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        sample_announcement_data: dict[str, Any],
    ) -> None:
        """Test POST /announcements creates a new announcement."""
        from app.models.user import User

        user = User(
            first_name="Test",
            last_name="Admin",
            email="admin@test.com",
            auth_id="test-admin-ann-123",
            role="admin",
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        announcement_data = {
            **sample_announcement_data,
            "user_id": str(user.user_id),
        }
        response = await async_client.post("/announcements/", json=announcement_data)
        assert response.status_code == 201
        data = response.json()
        assert data["subject"] == sample_announcement_data["subject"]
        assert data["message"] == sample_announcement_data["message"]
        assert data["user_id"] == str(user.user_id)
        assert "announcement_id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_get_announcement_by_id(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        sample_announcement_data: dict[str, Any],
    ) -> None:
        """Test GET /announcements/{id} returns the announcement."""
        from app.models.user import User

        user = User(
            first_name="Test",
            last_name="Admin",
            email="admin2@test.com",
            auth_id="test-admin-ann-456",
            role="admin",
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        create_data = {
            **sample_announcement_data,
            "user_id": str(user.user_id),
        }
        create_response = await async_client.post("/announcements/", json=create_data)
        announcement_id = create_response.json()["announcement_id"]

        response = await async_client.get(f"/announcements/{announcement_id}")
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
        async_client: AsyncClient,
        test_session: AsyncSession,
        sample_announcement_data: dict[str, Any],
    ) -> None:
        """Test PUT /announcements/{id} updates the announcement."""
        from app.models.user import User

        user = User(
            first_name="Test",
            last_name="Admin",
            email="admin3@test.com",
            auth_id="test-admin-ann-789",
            role="admin",
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        create_data = {
            **sample_announcement_data,
            "user_id": str(user.user_id),
        }
        create_response = await async_client.post("/announcements/", json=create_data)
        announcement_id = create_response.json()["announcement_id"]

        update_data = {"subject": "Updated Subject"}
        response = await async_client.put(
            f"/announcements/{announcement_id}", json=update_data
        )
        assert response.status_code == 200
        assert response.json()["subject"] == "Updated Subject"
        assert response.json()["message"] == sample_announcement_data["message"]

    @pytest.mark.asyncio
    async def test_delete_announcement(
        self,
        async_client: AsyncClient,
        test_session: AsyncSession,
        sample_announcement_data: dict[str, Any],
    ) -> None:
        """Test DELETE /announcements/{id} removes the announcement."""
        from app.models.user import User

        user = User(
            first_name="Test",
            last_name="Admin",
            email="admin4@test.com",
            auth_id="test-admin-ann-101",
            role="admin",
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        create_data = {
            **sample_announcement_data,
            "user_id": str(user.user_id),
        }
        create_response = await async_client.post("/announcements/", json=create_data)
        announcement_id = create_response.json()["announcement_id"]

        response = await async_client.delete(f"/announcements/{announcement_id}")
        assert response.status_code == 204

        get_response = await async_client.get(f"/announcements/{announcement_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_announcement_not_found(
        self, async_client: AsyncClient
    ) -> None:
        """Test DELETE /announcements/{id} returns 404 for nonexistent ID."""
        fake_id = uuid4()
        response = await async_client.delete(f"/announcements/{fake_id}")
        assert response.status_code == 404


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


class TestSystemSettingsRoutes:
    """Test suite for system settings API routes."""

    @pytest.mark.asyncio
    async def test_get_system_settings(self, async_client: AsyncClient) -> None:
        """GET /system-settings returns 200 (null-safe when unset)."""
        response = await async_client.get("/system-settings/")
        assert response.status_code == 200


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

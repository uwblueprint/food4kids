"""
Comprehensive integration tests for API routes.

Tests cover:
- Driver routes (CRUD operations)
- Location routes (CRUD operations)
- Route routes (read and delete operations)
- Route group routes (CRUD operations)
- Error handling (404s, validation errors)
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestDriverRoutes:
    """Test suite for driver API routes."""

    @pytest.mark.asyncio
    async def test_get_drivers_empty(self, async_client: AsyncClient) -> None:
        """Test GET /drivers returns empty list when no drivers exist."""
        response = await async_client.get("/drivers/")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_register_driver(
        self,
        async_client: AsyncClient,
        sample_driver_data: dict[str, Any],
    ) -> None:
        """Test POST /drivers creates a new driver."""
        mock_firebase_user = MagicMock()
        mock_firebase_user.uid = "fake-auth-id-123"

        fake_auth_dto = {
            "access_token": "fake-access-token",
            "name": sample_driver_data["name"],
            "id": str(uuid4()),
            "email": "newdriver@example.com",
        }
        # We don't want to actually call firebase so we mock the call
        with (
            patch("firebase_admin.auth.create_user", return_value=mock_firebase_user),
            patch("firebase_admin.auth.set_custom_user_claims"),
            patch(
                "app.services.implementations.auth_service.AuthService.generate_token",
                return_value=(fake_auth_dto, "fake_refresh_token"),
            ),
            patch(
                "app.services.implementations.auth_service.AuthService.send_email_verification_link"
            ),
        ):
            driver_register_data = {
                "name": sample_driver_data["name"],
                "email": "newdriver@example.com",
                "password": "testing123",
                "phone": sample_driver_data["phone"],
                "address": sample_driver_data["address"],
                "license_plate": sample_driver_data["license_plate"],
                "car_make_model": sample_driver_data["car_make_model"],
            }
            response = await async_client.post("/drivers/", json=driver_register_data)
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
        test_route: Any,  # noqa: ARG002
    ) -> None:
        """Test GET /routes returns paginated list of routes."""
        response = await async_client.get("/routes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)


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


class TestValidationErrors:
    """Test suite for validation error handling across routes."""

    @pytest.mark.asyncio
    async def test_create_driver_invalid_phone(self, async_client: AsyncClient) -> None:
        """Test POST /drivers with invalid phone number returns validation error."""
        invalid_data = {
            "name": "Test Driver",
            "email": "test@example.com",
            "password": "testing123",
            "phone": "invalid-phone",  # Invalid phone format
            "address": "123 Main St",
            "license_plate": "ABC123",
            "car_make_model": "Toyota Camry",
        }
        response = await async_client.post("/drivers/", json=invalid_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_location_missing_required_fields(
        self, async_client: AsyncClient
    ) -> None:
        """Test POST /locations with missing required fields returns validation error."""
        invalid_data = {
            "contact_name": "Jane Smith",
            # Missing: address, phone_number, longitude, latitude, halal, num_boxes
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
            name="Test Admin",
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
            name="Test Admin",
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
            name="Test Admin",
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
            name="Test Admin",
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

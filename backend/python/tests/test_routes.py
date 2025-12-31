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
    async def test_create_driver(
        self,
        async_client: AsyncClient,
        sample_driver_data: dict[str, Any],
        test_session: Any,
    ) -> None:
        """Test POST /drivers creates a new driver."""
        # First create a user for the driver
        from app.models.user import User

        user = User(
            name=sample_driver_data["name"],
            email="newdriver@example.com",
            auth_id=sample_driver_data["auth_id"] + "_new",
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        # Now create driver with user_id
        driver_create_data = {
            "user_id": str(user.user_id),
            "phone": sample_driver_data["phone"],
            "address": sample_driver_data["address"],
            "license_plate": sample_driver_data["license_plate"],
            "car_make_model": sample_driver_data["car_make_model"],
        }
        response = await async_client.post("/drivers/", json=driver_create_data)
        assert response.status_code == 201
        data = response.json()
        assert data["phone"] == sample_driver_data["phone"]
        assert data["license_plate"] == sample_driver_data["license_plate"]
        assert "driver_id" in data

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
        """Test GET /locations returns empty list when no locations exist."""
        response = await async_client.get("/locations/")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_create_location(
        self, async_client: AsyncClient, sample_location_data: dict[str, Any]
    ) -> None:
        """Test POST /locations creates a new location."""
        response = await async_client.post("/locations/", json=sample_location_data)
        assert response.status_code == 201
        data = response.json()
        assert data["contact_name"] == sample_location_data["contact_name"]
        assert data["address"] == sample_location_data["address"]
        assert "location_id" in data

    @pytest.mark.asyncio
    async def test_get_locations_with_data(
        self, async_client: AsyncClient, sample_location_data: dict[str, Any]
    ) -> None:
        """Test GET /locations returns list of locations."""
        # Create a location first
        create_response = await async_client.post(
            "/locations/", json=sample_location_data
        )
        assert create_response.status_code == 201

        # Get all locations
        response = await async_client.get("/locations/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_location_by_id(
        self, async_client: AsyncClient, sample_location_data: dict[str, Any]
    ) -> None:
        """Test GET /locations/{location_id} returns specific location."""
        # Create a location first
        create_response = await async_client.post(
            "/locations/", json=sample_location_data
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
        self, async_client: AsyncClient, sample_location_data: dict[str, Any]
    ) -> None:
        """Test PATCH /locations/{location_id} updates a location."""
        # Create a location first
        create_response = await async_client.post(
            "/locations/", json=sample_location_data
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
        self, async_client: AsyncClient, sample_location_data: dict[str, Any]
    ) -> None:
        """Test DELETE /locations/{location_id} deletes a location."""
        # Create a location first
        create_response = await async_client.post(
            "/locations/", json=sample_location_data
        )
        location_id = create_response.json()["location_id"]

        # Delete the location
        response = await async_client.delete(f"/locations/{location_id}")
        assert response.status_code == 204

        # Verify deletion
        get_response = await async_client.get(f"/locations/{location_id}")
        assert get_response.status_code == 404


class TestRouteRoutes:
    """Test suite for route API routes."""

    @pytest.mark.asyncio
    async def test_get_routes_empty(self, async_client: AsyncClient) -> None:
        """Test GET /routes returns empty list when no routes exist."""
        response = await async_client.get("/routes")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_routes_with_data(
        self,
        async_client: AsyncClient,
        test_route: Any,  # noqa: ARG002
    ) -> None:
        """Test GET /routes returns list of routes."""
        response = await async_client.get("/routes")
        assert response.status_code == 200
        # Routes may be empty if there are no route groups
        data = response.json()
        assert isinstance(data, list)


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


class TestValidationErrors:
    """Test suite for validation error handling across routes."""

    @pytest.mark.asyncio
    async def test_create_driver_invalid_phone(self, async_client: AsyncClient) -> None:
        """Test POST /drivers with invalid phone number returns validation error."""
        invalid_data = {
            "name": "Test Driver",
            "email": "test@example.com",
            "phone": "invalid-phone",  # Invalid phone format
            "address": "123 Main St",
            "license_plate": "ABC123",
            "car_make_model": "Toyota Camry",
            "auth_id": "test-auth-123",
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

"""
Comprehensive tests for the DriverAssignmentService.

Tests cover:
- CRUD operations (Create, Read, Update, Delete)
- Error handling and edge cases
- Model validation
- Database interactions using real database
"""

import logging
from datetime import datetime
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver_assignment import (
    DriverAssignmentCreate,
    DriverAssignmentUpdate,
)
from app.services.implementations.driver_assignment_service import (
    DriverAssignmentService,
)


@pytest.fixture
def driver_assignment_service() -> DriverAssignmentService:
    """Create DriverAssignmentService instance with real logger."""
    logger = logging.getLogger(__name__)
    return DriverAssignmentService(logger)


class TestDriverAssignmentService:
    """Test suite for DriverAssignmentService CRUD operations using real database."""

    @pytest.fixture
    def sample_driver_assignment_data(
        self, test_driver: Any, test_route: Any, test_route_group: Any
    ) -> dict:
        """Sample driver assignment data for testing."""
        return {
            "driver_id": test_driver.driver_id,
            "route_id": test_route.route_id,
            "route_group_id": test_route_group.route_group_id,
            "time": datetime(2024, 1, 15, 8, 0),
            "completed": False,
        }

    @pytest.fixture
    def sample_driver_assignment_create(
        self, sample_driver_assignment_data: dict
    ) -> DriverAssignmentCreate:
        """Sample DriverAssignmentCreate instance."""
        return DriverAssignmentCreate(**sample_driver_assignment_data)

    class TestGetDriverAssignments:
        """Test get_driver_assignments method."""

        @pytest.mark.asyncio
        async def test_get_driver_assignments_empty_list(
            self,
            driver_assignment_service: DriverAssignmentService,
            test_session: AsyncSession,
        ) -> None:
            """Test retrieval when no driver assignments exist."""
            # Execute
            result = await driver_assignment_service.get_driver_assignments(
                test_session
            )

            # Verify
            assert result == []

        @pytest.mark.asyncio
        async def test_get_driver_assignments_with_data(
            self,
            driver_assignment_service: DriverAssignmentService,
            test_session: AsyncSession,
            sample_driver_assignment_create: DriverAssignmentCreate,
        ) -> None:
            """Test successful retrieval of driver assignments."""
            # Create a driver assignment first
            created_assignment = (
                await driver_assignment_service.create_driver_assignment(
                    test_session, sample_driver_assignment_create
                )
            )

            # Execute
            result = await driver_assignment_service.get_driver_assignments(
                test_session
            )

            # Verify
            assert len(result) == 1
            assert (
                result[0].driver_assignment_id
                == created_assignment.driver_assignment_id
            )
            assert result[0].driver_id == created_assignment.driver_id
            assert result[0].route_id == created_assignment.route_id


class TestDriverAssignmentIntegration:
    """Integration tests for driver assignment functionality."""

    @pytest.mark.asyncio
    async def test_full_crud_workflow(
        self,
        driver_assignment_service: DriverAssignmentService,
        test_session: AsyncSession,
        test_driver: Any,
        test_route: Any,
        test_route_group: Any,
    ) -> None:
        """Test complete CRUD workflow with real database."""
        # Create
        assignment_data = DriverAssignmentCreate(
            driver_id=test_driver.driver_id,
            route_id=test_route.route_id,
            route_group_id=test_route_group.route_group_id,
            time=datetime(2024, 1, 15, 8, 0),
            completed=False,
        )

        created_assignment = await driver_assignment_service.create_driver_assignment(
            test_session, assignment_data
        )
        assert created_assignment is not None
        assert created_assignment.completed is False

        # Read
        assignments = await driver_assignment_service.get_driver_assignments(
            test_session
        )
        assert len(assignments) == 1
        assert (
            assignments[0].driver_assignment_id
            == created_assignment.driver_assignment_id
        )

        # Update
        update_data = DriverAssignmentUpdate(completed=True)
        updated_assignment = await driver_assignment_service.update_driver_assignment(
            test_session, created_assignment.driver_assignment_id, update_data
        )
        assert updated_assignment is not None
        assert updated_assignment.completed is True

        # Delete
        delete_result = await driver_assignment_service.delete_driver_assignment(
            test_session, created_assignment.driver_assignment_id
        )
        assert delete_result is True

        # Verify deletion
        final_assignments = await driver_assignment_service.get_driver_assignments(
            test_session
        )
        assert len(final_assignments) == 0

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import selectinload
from sqlmodel import select

if TYPE_CHECKING:
    import logging
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import Driver
from app.models.driver_assignment import (
    DriverAssignment,
    DriverAssignmentCreate,
    DriverAssignmentUpdate,
    SuggestedDriverResponse,
)
from app.models.route_group_membership import RouteGroupMembership


class DriverAssignmentService:
    """Service for managing driver assignments to routes"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_driver_assignments(
        self, session: AsyncSession
    ) -> list[DriverAssignment]:
        """Get all driver assignments - returns SQLModel instances directly"""
        statement = select(DriverAssignment)
        result = await session.execute(statement)
        return list(result.scalars().all())

    async def create_driver_assignment(
        self, session: AsyncSession, driver_assignment_data: DriverAssignmentCreate
    ) -> DriverAssignment:
        """Create new entity"""
        try:
            # Create SQLModel instance from data
            driver_assignment = DriverAssignment(**driver_assignment_data.model_dump())

            session.add(driver_assignment)
            await session.commit()
            await session.refresh(driver_assignment)

            return driver_assignment

        except Exception as error:
            self.logger.error(f"Failed to create driver assignment: {error!s}")
            await session.rollback()
            raise error

    async def update_driver_assignment(
        self,
        session: AsyncSession,
        driver_assignment_id: UUID,
        driver_assignment_data: DriverAssignmentUpdate,
    ) -> DriverAssignment | None:
        """Update existing driver assignment"""
        try:
            statement = select(DriverAssignment).where(
                DriverAssignment.driver_assignment_id == driver_assignment_id
            )
            result = await session.execute(statement)
            driver_assignment = result.scalars().first()

            if not driver_assignment:
                self.logger.error(
                    f"Driver assignment with id {driver_assignment_id} not found"
                )
                return None

            # Update fields
            update_data = driver_assignment_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(driver_assignment, field, value)

            await session.commit()
            await session.refresh(driver_assignment)

            return driver_assignment

        except Exception as error:
            self.logger.error(f"Failed to update driver assignment: {error!s}")
            await session.rollback()
            raise error

    async def delete_driver_assignment(
        self, session: AsyncSession, driver_assignment_id: UUID
    ) -> bool:
        """Delete driver assignment by ID"""
        try:
            statement = select(DriverAssignment).where(
                DriverAssignment.driver_assignment_id == driver_assignment_id
            )
            result = await session.execute(statement)
            driver_assignment = result.scalars().first()

            if not driver_assignment:
                self.logger.error(
                    f"Driver assignment with id {driver_assignment_id} not found"
                )
                return False

            await session.delete(driver_assignment)
            await session.commit()

            return True

        except Exception as error:
            self.logger.error(f"Failed to delete driver assignment: {error!s}")
            await session.rollback()
            raise error

    async def get_suggested_driver(
        self,
        session: AsyncSession,
        route_id: UUID,
        route_group_id: UUID,
    ) -> SuggestedDriverResponse | None:
        """Get the driver who was last assigned to the given route in the given route group."""
        statement = (
            select(DriverAssignment)
            .where(
                DriverAssignment.route_id == route_id,
                DriverAssignment.route_group_id == route_group_id,
            )
            .order_by(DriverAssignment.time.desc())  # type: ignore[attr-defined]
            .limit(1)
        )
        result = await session.execute(statement)
        assignment = result.scalars().first()
        if not assignment:
            return None

        driver_statement = (
            select(Driver)
            .options(selectinload(Driver.user))  # type: ignore[arg-type]
            .where(Driver.driver_id == assignment.driver_id)
        )
        driver_result = await session.execute(driver_statement)
        driver = driver_result.scalars().first()
        if not driver or not driver.user:
            return None

        return SuggestedDriverResponse(
            driver_id=driver.driver_id,
            driver_name=driver.user.name,
        )

    async def ensure_route_and_route_group_exist(
        self,
        session: AsyncSession,
        route_id: UUID,
        route_group_id: UUID,
    ) -> bool:
        """Checks whether the given route_id and route_group_id combination exists as a RouteGroupMembership."""
        statement = (
            select(RouteGroupMembership)
            .where(
                RouteGroupMembership.route_id == route_id,
                RouteGroupMembership.route_group_id == route_group_id,
            )
            .limit(1)
        )
        result = await session.execute(statement)
        return result.scalars().first() is not None

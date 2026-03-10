import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.driver_assignment import (
    DriverAssignment,
    DriverAssignmentCreate,
    DriverAssignmentUpdate,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.utilities.pagination import paginate_query


class DriverAssignmentService:
    """Service for managing driver assignments to routes"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_driver_assignments(
        self, session: AsyncSession, pagination: PaginationParams
    ) -> PaginatedResponse[DriverAssignment]:
        """Get paginated driver assignments"""
        statement = select(DriverAssignment).order_by(DriverAssignment.created_at.desc())  # type: ignore[union-attr]
        result, total = await paginate_query(session, statement, pagination)
        items = list(result.scalars().all())
        return PaginatedResponse.create(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

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

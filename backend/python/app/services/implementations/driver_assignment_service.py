import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver_assignment import (
    DriverAssignment,
    DriverAssignmentCreate,
)


class DriverAssignmentService:
    """Modern FastAPI-style driver assignment service"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

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

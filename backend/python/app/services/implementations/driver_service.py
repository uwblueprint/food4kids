import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.models.driver import Driver, DriverCreate, DriverUpdate
from app.models.user import User


class DriverService:
    """Service for managing drivers with Firebase authentication integration"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_driver_by_id(
        self, session: AsyncSession, driver_id: UUID
    ) -> Driver | None:
        """Get driver by ID - returns SQLModel instance"""
        try:
            statement = (
                select(Driver)
                .options(selectinload(Driver.user))  # type: ignore[arg-type]
                .where(Driver.driver_id == driver_id)
            )
            result = await session.execute(statement)
            driver = result.scalars().first()

            if not driver:
                self.logger.error(f"Driver with id {driver_id} not found")
                return None

            return driver
        except Exception as e:
            self.logger.error(f"Failed to get driver by id: {e!s}")
            raise e

    async def get_driver_by_email(
        self, session: AsyncSession, email: str
    ) -> Driver | None:
        """Get driver by email using Firebase"""
        try:
            statement = (
                select(Driver)
                .options(selectinload(Driver.user))  # type: ignore[arg-type]
                .join(Driver.user)  # type: ignore[arg-type]
                .where(User.email == email)
            )
            result = await session.execute(statement)
            driver = result.scalars().first()

            if not driver:
                self.logger.error(f"Driver with email {email} not found")
                return None

            return driver
        except Exception as e:
            self.logger.error(f"Failed to get driver by email: {e!s}")
            raise e

    # TODO: auth is being changed right now, make sure this still works/is relevant
    async def get_driver_by_auth_id(
        self, session: AsyncSession, auth_id: str
    ) -> Driver | None:
        """Get driver by auth_id"""
        try:
            statement = (
                select(Driver)
                .options(selectinload(Driver.user))  # type: ignore[arg-type]
                .join(Driver.user)  # type: ignore[arg-type]
                .where(User.auth_id == auth_id)
            )
            result = await session.execute(statement)
            driver = result.scalars().first()

            if not driver:
                self.logger.error(f"Driver with auth_id {auth_id} not found")
                return None

            return driver
        except Exception as e:
            self.logger.error(f"Failed to get driver by auth_id: {e!s}")
            raise e

    async def get_drivers(self, session: AsyncSession) -> list[Driver]:
        """Get all drivers - returns SQLModel instances"""
        try:
            statement = select(Driver).options(selectinload(Driver.user))  # type: ignore[arg-type]
            result = await session.execute(statement)
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get drivers: {e!s}")
            raise e

    async def create_driver(
        self,
        session: AsyncSession,
        driver_data: DriverCreate,
    ) -> Driver:
        """Create new driver with Firebase integration"""
        driver = Driver(
            user_id=driver_data.user_id,
            address=driver_data.address,
            phone=driver_data.phone,
            partner_driver_name=driver_data.partner_driver_name,
            availability=driver_data.availability,
            license_plate=driver_data.license_plate,
            car_make_model=driver_data.car_make_model,
            active=driver_data.active,
            notes=driver_data.notes,
        )

        session.add(driver)
        await session.flush()
        return driver

    async def update_driver_by_id(
        self, session: AsyncSession, driver_id: UUID, driver_data: DriverUpdate
    ) -> Driver | None:
        """Update driver by ID"""
        driver: Driver | None = None
        old_values: dict[str, Any] = {}
        try:
            statement = (
                select(Driver)
                .options(selectinload(Driver.user))  # type: ignore[arg-type]
                .where(Driver.driver_id == driver_id)
            )
            result = await session.execute(statement)
            driver = result.scalars().first()

            if not driver:
                self.logger.error(f"Driver with id {driver_id} not found")
                return None

            update_data = driver_data.model_dump(exclude_unset=True)
            old_values = {field: getattr(driver, field) for field in update_data}

            for field, value in update_data.items():
                setattr(driver, field, value)

            await session.commit()
            await session.refresh(driver, attribute_names=["user"])
            return driver

        except Exception as e:
            # Rollback database changes
            assert driver is not None
            for field, value in old_values.items():
                setattr(driver, field, value)
            await session.commit()
            self.logger.error(f"Failed to update driver: {e!s}")
            raise e

    async def delete_driver_by_id(self, session: AsyncSession, driver_id: UUID) -> None:
        """Delete driver by ID"""
        try:
            statement = select(Driver).where(Driver.driver_id == driver_id)
            result = await session.execute(statement)
            driver = result.scalars().first()

            if not driver:
                self.logger.error(f"Driver with id {driver_id} not found")
                return

            await session.delete(driver)
            await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to delete driver: {e!s}")
            raise e

    async def get_auth_id_by_driver_id(
        self, session: AsyncSession, driver_id: UUID
    ) -> str | None:
        """Get auth_id by driver_id"""
        try:
            statement = (
                select(Driver)
                .options(selectinload(Driver.user))  # type: ignore[arg-type]
                .where(Driver.driver_id == driver_id)
            )
            result = await session.execute(statement)
            driver = result.scalars().first()

            if not driver:
                self.logger.error(f"Driver with id {driver_id} not found")
                return None

            return driver.user.auth_id
        except Exception as e:
            self.logger.error(f"Failed to get auth_id by driver_id: {e!s}")
            raise e

    async def get_driver_id_by_auth_id(
        self, session: AsyncSession, auth_id: str
    ) -> UUID | None:
        """Get driver_id by auth_id"""
        try:
            statement = (
                select(Driver)
                .options(selectinload(Driver.user))  # type: ignore[arg-type]
                .join(Driver.user)  # type: ignore[arg-type]
                .where(User.auth_id == auth_id)
            )
            result = await session.execute(statement)
            driver = result.scalars().first()

            if not driver:
                self.logger.error(f"Driver with auth_id {auth_id} not found")
                return None

            return driver.driver_id
        except Exception as e:
            self.logger.error(f"Failed to get driver_id by auth_id: {e!s}")
            raise e

    async def delete_driver_by_email(self, session: AsyncSession, email: str) -> None:
        """Delete driver by email"""
        try:
            statement = select(Driver).join(Driver.user).where(User.email == email)  # type: ignore[arg-type]
            result = await session.execute(statement)
            driver = result.scalars().first()

            if not driver:
                self.logger.error(f"Driver with email {email} not found")
                return

            await session.delete(driver)
            await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to delete driver by email: {e!s}")
            raise e

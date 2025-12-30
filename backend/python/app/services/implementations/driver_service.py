import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.models.driver import Driver, DriverCreate, DriverUpdate
from app.models.user import User


class DriverService:
    """Modern FastAPI-style driver service"""

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

    async def get_driver_by_auth_id(
        self, session: AsyncSession, auth_id: str
    ) -> Driver | None:
        """Get driver by auth_id"""
        try:
            statement = (
                select(Driver)
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
        try:
            driver = Driver(
                user_id=driver_data.user_id,
                address=driver_data.address,
                phone=driver_data.phone,
                license_plate=driver_data.license_plate,
                car_make_model=driver_data.car_make_model,
                active=driver_data.active,
                notes=driver_data.notes,
            )

            try:
                session.add(driver)
                await session.commit()
                await session.refresh(driver, attribute_names=["user"])
                return driver

            except Exception as db_error:
                raise db_error

        except Exception as e:
            self.logger.error(f"Failed to create driver: {e!s}")
            raise e

    async def update_driver_by_id(
        self, session: AsyncSession, driver_id: UUID, driver_data: DriverUpdate
    ) -> Driver | None:
        """Update driver by ID"""
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

            # Store old values for rollback
            old_phone = driver.phone
            old_address = driver.address
            old_license_plate = driver.license_plate
            old_car_make_model = driver.car_make_model
            old_active = driver.active
            old_notes = driver.notes

            # Update driver fields
            if driver_data.phone is not None:
                driver.phone = driver_data.phone
            if driver_data.address is not None:
                driver.address = driver_data.address
            if driver_data.license_plate is not None:
                driver.license_plate = driver_data.license_plate
            if driver_data.car_make_model is not None:
                driver.car_make_model = driver_data.car_make_model
            if driver_data.active is not None:
                driver.active = driver_data.active
            if driver_data.notes is not None:
                driver.notes = driver_data.notes

            await session.commit()
            await session.refresh(driver, attribute_names=["user"])
            return driver

        except Exception as e:
            # Rollback database changes
            assert driver is not None
            driver.phone = old_phone
            driver.address = old_address
            driver.license_plate = old_license_plate
            driver.car_make_model = old_car_make_model
            driver.active = old_active
            driver.notes = old_notes
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
            statement = select(Driver).where(Driver.driver_id == driver_id)
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
            statement = (
                select(Driver)
                .join(Driver.user)  # type: ignore[arg-type]
                .where(User.email == email)
            )
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

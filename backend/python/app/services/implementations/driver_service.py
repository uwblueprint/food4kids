import logging
from typing import TYPE_CHECKING
from uuid import UUID

import firebase_admin.auth
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.driver import Driver, DriverCreate, DriverUpdate

if TYPE_CHECKING:
    from firebase_admin.auth import UserRecord


class DriverService:
    """Modern FastAPI-style driver service"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_driver_by_id(
        self, session: AsyncSession, driver_id: UUID
    ) -> Driver | None:
        """Get driver by ID - returns SQLModel instance"""
        try:
            statement = select(Driver).where(Driver.driver_id == driver_id)
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
            firebase_user: UserRecord = firebase_admin.auth.get_user_by_email(email)
            statement = select(Driver).where(Driver.auth_id == firebase_user.uid)
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
            statement = select(Driver).where(Driver.auth_id == auth_id)
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
            statement = select(Driver)
            result = await session.execute(statement)
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get drivers: {e!s}")
            raise e

    async def create_driver(
        self,
        session: AsyncSession,
        driver_data: DriverCreate,
        auth_id: str | None = None,
        signup_method: str = "PASSWORD",
    ) -> Driver:
        """Create new driver with Firebase integration"""
        firebase_user: UserRecord | None = None

        try:
            # Create Firebase user
            if signup_method == "PASSWORD":
                firebase_user = firebase_admin.auth.create_user(
                    email=driver_data.email, password=driver_data.password
                )
            elif signup_method == "GOOGLE":
                firebase_user = firebase_admin.auth.get_user(uid=auth_id)

            # Create database driver
            if firebase_user is None:
                raise Exception("Failed to create Firebase user")

            driver = Driver(
                name=driver_data.name,
                email=driver_data.email,
                phone=driver_data.phone,
                address=driver_data.address,
                license_plate=driver_data.license_plate,
                car_make_model=driver_data.car_make_model,
                active=driver_data.active,
                notes=driver_data.notes,
                auth_id=firebase_user.uid,
            )

            try:
                session.add(driver)
                await session.commit()
                await session.refresh(driver)
                return driver

            except Exception as db_error:
                # Rollback Firebase user creation
                try:
                    firebase_admin.auth.delete_user(firebase_user.uid)
                except Exception as firebase_error:
                    self.logger.error(
                        f"Failed to rollback Firebase user: {firebase_error!s}"
                    )
                raise db_error

        except Exception as e:
            self.logger.error(f"Failed to create driver: {e!s}")
            raise e

    async def update_driver_by_id(
        self, session: AsyncSession, driver_id: UUID, driver_data: DriverUpdate
    ) -> Driver | None:
        """Update driver by ID"""
        try:
            statement = select(Driver).where(Driver.driver_id == driver_id)
            result = await session.execute(statement)
            driver = result.scalars().first()

            if not driver:
                self.logger.error(f"Driver with id {driver_id} not found")
                return None

            # Store old values for rollback
            old_name = driver.name
            old_email = driver.email
            old_phone = driver.phone
            old_address = driver.address
            old_license_plate = driver.license_plate
            old_car_make_model = driver.car_make_model
            old_active = driver.active
            old_notes = driver.notes

            # Update driver fields
            if driver_data.name is not None:
                driver.name = driver_data.name
            if driver_data.email is not None:
                driver.email = driver_data.email
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

            # Update Firebase email
            try:
                if driver_data.email is not None:
                    firebase_admin.auth.update_user(
                        driver.auth_id, email=driver_data.email
                    )
                await session.refresh(driver)
                return driver

            except Exception as firebase_error:
                # Rollback database changes
                driver.name = old_name
                driver.email = old_email
                driver.phone = old_phone
                driver.address = old_address
                driver.license_plate = old_license_plate
                driver.car_make_model = old_car_make_model
                driver.active = old_active
                driver.notes = old_notes
                await session.commit()
                raise firebase_error

        except Exception as e:
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

            # Store for rollback
            driver_data = {
                "name": driver.name,
                "email": driver.email,
                "phone": driver.phone,
                "address": driver.address,
                "license_plate": driver.license_plate,
                "car_make_model": driver.car_make_model,
                "active": driver.active,
                "notes": driver.notes,
                "auth_id": driver.auth_id,
            }

            await session.delete(driver)
            await session.commit()

            # Delete from Firebase
            try:
                firebase_admin.auth.delete_user(driver.auth_id)

            except Exception as firebase_error:
                # Rollback database deletion
                new_driver = Driver(**driver_data)
                session.add(new_driver)
                await session.commit()
                raise firebase_error

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

            return driver.auth_id
        except Exception as e:
            self.logger.error(f"Failed to get auth_id by driver_id: {e!s}")
            raise e

    async def get_driver_id_by_auth_id(
        self, session: AsyncSession, auth_id: str
    ) -> UUID | None:
        """Get driver_id by auth_id"""
        try:
            statement = select(Driver).where(Driver.auth_id == auth_id)
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
            firebase_user: UserRecord = firebase_admin.auth.get_user_by_email(email)
            statement = select(Driver).where(Driver.auth_id == firebase_user.uid)
            result = await session.execute(statement)
            driver = result.scalars().first()

            if not driver:
                self.logger.error(f"Driver with email {email} not found")
                return

            # Store for rollback
            driver_data = {
                "name": driver.name,
                "email": driver.email,
                "phone": driver.phone,
                "address": driver.address,
                "license_plate": driver.license_plate,
                "car_make_model": driver.car_make_model,
                "active": driver.active,
                "notes": driver.notes,
                "auth_id": driver.auth_id,
            }

            await session.delete(driver)
            await session.commit()

            # Delete from Firebase
            try:
                firebase_admin.auth.delete_user(driver.auth_id)

            except Exception as firebase_error:
                # Rollback database deletion
                new_driver = Driver(**driver_data)
                session.add(new_driver)
                await session.commit()
                raise firebase_error

        except Exception as e:
            self.logger.error(f"Failed to delete driver by email: {e!s}")
            raise e

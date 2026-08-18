import logging
from datetime import date
from typing import Any, ClassVar, Literal
from uuid import UUID

import firebase_admin.auth
from sqlalchemy import and_, case, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.models.driver import (
    Driver,
    DriverCreate,
    DriverListRead,
    DriverRead,
    DriverUpdate,
)
from app.models.enum import NotePermission
from app.models.note_chain import NoteChain
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_snapshot import RouteSnapshot
from app.models.user import User
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.utilities.pagination import paginate_query


class DriverService:
    """Service for managing drivers with Firebase authentication integration"""

    USER_UPDATE_FIELDS: ClassVar[set[str]] = {"first_name", "last_name"}

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

    async def get_driver_list(
        self,
        session: AsyncSession,
        pagination: PaginationParams,
        search: str | None = None,
        sort_by: Literal[
            "name", "current_year_km", "last_year_km", "last_delivery"
        ] = "name",
        order: Literal["asc", "desc"] = "asc",
    ) -> PaginatedResponse[DriverListRead]:
        """Return a page of driver rows with list-level activity aggregates."""
        today = date.today()
        current_year_start = date(today.year, 1, 1)
        last_year_start = date(today.year - 1, 1, 1)

        mileage = (
            select(
                Route.driver_id.label("driver_id"),
                func.sum(
                    case(
                        (RouteGroup.drive_date >= current_year_start, Route.length),
                        else_=0,
                    )
                ).label("current_year_km"),
                func.sum(
                    case(
                        (
                            and_(
                                RouteGroup.drive_date >= last_year_start,
                                RouteGroup.drive_date < current_year_start,
                            ),
                            Route.length,
                        ),
                        else_=0,
                    )
                ).label("last_year_km"),
                func.max(RouteGroup.drive_date).label("last_delivery"),
            )
            .join(RouteGroup, RouteGroup.route_group_id == Route.route_group_id)
            .join(RouteSnapshot, RouteSnapshot.route_id == Route.route_id)
            .where(Route.driver_id.is_not(None))
            .group_by(Route.driver_id)
            .subquery()
        )
        activity = (
            select(Route.driver_id.label("driver_id"))
            .join(RouteGroup, RouteGroup.route_group_id == Route.route_group_id)
            .where(Route.driver_id.is_not(None), RouteGroup.drive_date >= today)
            .group_by(Route.driver_id)
            .subquery()
        )

        current_km = func.coalesce(mileage.c.current_year_km, 0)
        last_km = func.coalesce(mileage.c.last_year_km, 0)
        statement = (
            select(
                Driver,
                current_km.label("current_year_km"),
                last_km.label("last_year_km"),
                mileage.c.last_delivery,
                activity.c.driver_id.is_not(None).label("is_active"),
            )
            .options(selectinload(Driver.user))  # type: ignore[arg-type]
            .join(User, User.user_id == Driver.user_id)
            .outerjoin(mileage, mileage.c.driver_id == Driver.driver_id)
            .outerjoin(activity, activity.c.driver_id == Driver.driver_id)
        )
        if search and (term := search.strip()):
            pattern = f"%{term}%"
            statement = statement.where(
                or_(
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                    (User.first_name + " " + User.last_name).ilike(pattern),
                )
            )

        sort_columns = {
            "name": (User.first_name, User.last_name),
            "current_year_km": (current_km,),
            "last_year_km": (last_km,),
            "last_delivery": (mileage.c.last_delivery,),
        }
        columns = sort_columns[sort_by]
        statement = statement.order_by(
            *(
                column.desc().nulls_last()
                if order == "desc"
                else column.asc().nulls_last()
                for column in columns
            ),
            Driver.driver_id,
        )
        result, total = await paginate_query(session, statement, pagination)
        rows = [
            DriverListRead(
                **DriverRead.model_validate(driver).model_dump(),
                current_year_km=float(current_year_km_value),
                last_year_km=float(last_year_km_value),
                last_delivery=last_delivery,
                is_active=is_active,
            )
            for driver, current_year_km_value, last_year_km_value, last_delivery, is_active in result.all()
        ]
        return PaginatedResponse.create(
            rows, total, pagination.page, pagination.page_size
        )

    async def create_driver(
        self,
        session: AsyncSession,
        driver_data: DriverCreate,
    ) -> Driver:
        """Create new driver with Firebase integration"""
        # Auto-create an admin-only note chain so admins can leave notes about
        # the driver that the driver themselves cannot read or write.
        note_chain = NoteChain(
            read_permission=NotePermission.ADMIN,
            write_permission=NotePermission.ADMIN,
        )
        session.add(note_chain)
        await session.flush()

        driver = Driver(
            user_id=driver_data.user_id,
            address=driver_data.address,
            phone=driver_data.phone,
            partner_driver_name=driver_data.partner_driver_name,
            availability=driver_data.availability,
            license_plate=driver_data.license_plate,
            car_make_model=driver_data.car_make_model,
            active=driver_data.active,
            note_chain_id=note_chain.note_chain_id,
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
            old_values = {
                field: getattr(
                    driver.user if field in self.USER_UPDATE_FIELDS else driver, field
                )
                for field in update_data
            }

            for field, value in update_data.items():
                target = driver.user if field in self.USER_UPDATE_FIELDS else driver
                setattr(target, field, value)

            await session.commit()

            if (
                self.USER_UPDATE_FIELDS.intersection(update_data)
                and driver.user.auth_id is not None
            ):
                firebase_admin.auth.update_user(
                    driver.user.auth_id,
                    display_name=driver.user.full_name,
                )
                firebase_admin.auth.set_custom_user_claims(
                    driver.user.auth_id,
                    {
                        "role": driver.user.role,
                        "given_name": driver.user.first_name,
                        "family_name": driver.user.last_name,
                    },
                )

            await session.refresh(driver, attribute_names=["user"])
            return driver

        except Exception as e:
            # Rollback database changes
            assert driver is not None
            for field, value in old_values.items():
                target = driver.user if field in self.USER_UPDATE_FIELDS else driver
                setattr(target, field, value)
            await session.commit()
            self.logger.error(f"Failed to update driver: {e!s}")
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

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, exists
from sqlalchemy import select as sql_select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.driver_assignment import DriverAssignment
from app.models.route import Route, RouteWithDateRead
from app.models.route_group import RouteGroup
from app.models.route_group_membership import RouteGroupMembership


class RouteService:
    """
    Service class for handling route-related operations.

    This class provides methods to manage Route entities, such as deleting routes by their ID.
    While currently only the delete operation is implemented, this class is intended to be extended
    with additional route-related operations in the future.
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_routes(
        self,
        session: AsyncSession,
        unassigned_only: bool = False,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[RouteWithDateRead]:
        """
        Get routes with optional filtering for unassigned routes and date range.
        Returns routes with their drive dates - routes can appear multiple times for different dates.
        When unassigned_only is False, returns all routes (no assignment filter).
        When unassigned_only is True, returns only routes that are unassigned for the given route group.
        """
        statement = (
            select(
                Route,
                RouteGroup.route_group_id,
                RouteGroup.drive_date,
            )
            .join(RouteGroupMembership, Route.route_id == RouteGroupMembership.route_id)  # type: ignore[arg-type]
            .join(
                RouteGroup,
                RouteGroupMembership.route_group_id == RouteGroup.route_group_id,  # type: ignore[arg-type]
            )
        )

        # Parse and filter by date range
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            statement = statement.where(RouteGroup.drive_date >= start_dt)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            statement = statement.where(RouteGroup.drive_date <= end_dt)

        # Filter for unassigned routes only
        if unassigned_only:
            statement = statement.where(
                ~exists(
                    sql_select(1)
                    .select_from(DriverAssignment)
                    .where(
                        and_(
                            DriverAssignment.route_id == Route.route_id,  # type: ignore[arg-type]
                            DriverAssignment.route_group_id
                            == RouteGroup.route_group_id,  # type: ignore[arg-type]
                        )
                    )
                )
            )

        statement = statement.order_by(RouteGroup.drive_date, Route.name)  # type: ignore[arg-type]

        result = await session.execute(statement)
        rows = result.all()

        # Return RouteWithDateRead objects - no deduplication, routes can appear multiple times for different dates
        return [
            RouteWithDateRead(
                route_id=row.Route.route_id,
                name=row.Route.name,
                notes=row.Route.notes,
                length=row.Route.length,
                drive_date=row.drive_date,
            )
            for row in rows
        ]

    async def get_route(self, session: AsyncSession, route_id: UUID) -> Route:
        try:
            """Get route by ID"""
            statement = select(Route).where(Route.route_id == route_id)
            result = await session.execute(statement)
            route = result.scalars().first()

            if not route:
                self.logger.error(f"Route with id {route_id} not found")
                raise ValueError(f"Route with id {route_id} not found")

            return route
        except Exception as error:
            self.logger.error(f"Failed to get route {route_id}: {error!s}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Failed to retrieve route.")

    async def delete_route(self, session: AsyncSession, route_id: UUID) -> bool:
        """Delete route by ID"""
        try:
            statement = select(Route).where(Route.route_id == route_id)
            result = await session.execute(statement)
            route = result.scalars().first()

            if not route:
                self.logger.error(f"Route with id {route_id} not found")
                return False

            await session.delete(route)
            await session.commit()

            return True
        except Exception as error:
            self.logger.error(f"Failed to delete route {route_id}: {error!s}")
            await session.rollback()
            # TODO: do we really want to return the raw error
            raise error

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import exists, func, select as sql_select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.driver_assignment import DriverAssignment
from app.models.route import Route
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
        unassigned: bool = False,
        start_date: str | None = None,
        end_date: str | None = None,
    ):
        """
        Get routes with optional filtering for unassigned routes and date range
        """
        statement = (
            select(
                Route,
                RouteGroup.drive_date,
            )
            .join(RouteGroupMembership, Route.route_id == RouteGroupMembership.route_id)
            .join(RouteGroup, RouteGroupMembership.route_group_id == RouteGroup.route_group_id)
        )

        # Parse and filter by date range
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            statement = statement.where(RouteGroup.drive_date >= start_dt)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            statement = statement.where(RouteGroup.drive_date <= end_dt)

        # Filter for unassigned routes
        if unassigned:
            statement = statement.where(
                ~exists(
                    sql_select(1)
                    .select_from(DriverAssignment)
                    .where(DriverAssignment.route_id == Route.route_id)
                )
            )

        statement = statement.order_by(RouteGroup.drive_date, Route.name)

        result = await session.execute(statement)
        rows = result.all()

        return [
            {
                "route_id": str(row.Route.route_id),
                "name": row.Route.name,
                "notes": row.Route.notes,
                "length": row.Route.length,
            }
            for row in rows
        ]

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
            raise error

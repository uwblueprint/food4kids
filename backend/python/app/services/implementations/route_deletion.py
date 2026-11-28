from datetime import date
from enum import StrEnum
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlmodel import SQLModel, col, select

from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_snapshot import RouteSnapshot
from app.models.route_stop import RouteStop
from app.utilities.datetime_utils import today_local


class RouteDeletionBlockCode(StrEnum):
    PAST_DATE = "past_date"
    COMPLETED_ROUTE = "completed_route"


BLOCK_MESSAGES = {
    RouteDeletionBlockCode.PAST_DATE: "Past routes and route groups cannot be deleted.",
    RouteDeletionBlockCode.COMPLETED_ROUTE: (
        "Completed routes and route groups containing them cannot be deleted."
    ),
}


class RouteDeletionImpact(SQLModel):
    name: str
    drive_date: date
    num_routes: int
    num_stops: int
    num_drivers: int
    num_unrouted_locations: int
    blocked_reason: str | None
    blocked_code: RouteDeletionBlockCode | None


async def get_deletion_scope(
    session: AsyncSession, target_id: UUID, *, individual: bool, lock: bool = False
) -> tuple[RouteGroup | None, list[Route]]:
    group_query = select(RouteGroup)
    if individual:
        group_query = group_query.join(
            Route, col(Route.route_group_id) == col(RouteGroup.route_group_id)
        ).where(Route.route_id == target_id)
    else:
        group_query = group_query.where(RouteGroup.route_group_id == target_id)
    if lock:
        # Take the group lock first for both delete paths. It protects the
        # drive date and prevents new routes from being added to the group.
        group_query = group_query.with_for_update(of=RouteGroup)
    group = (await session.execute(group_query)).scalar_one_or_none()
    if group is None:
        return None, []

    routes_query = select(Route).where(Route.route_group_id == group.route_group_id)
    if individual:
        routes_query = routes_query.where(Route.route_id == target_id)
    if lock:
        # Lock the routes before checking for snapshots. A concurrent snapshot
        # insert takes a foreign key lock on its parent route.
        routes_query = routes_query.order_by(col(Route.route_id)).with_for_update()
    routes = list((await session.scalars(routes_query)).all())
    return (None, []) if individual and not routes else (group, routes)


async def get_deletion_block_code(
    session: AsyncSession, group: RouteGroup, route_ids: list[UUID]
) -> RouteDeletionBlockCode | None:
    if group.drive_date < today_local():
        return RouteDeletionBlockCode.PAST_DATE
    snapshot = await session.scalar(
        select(RouteSnapshot.route_id)
        .where(col(RouteSnapshot.route_id).in_(route_ids))
        .limit(1)
    )
    if snapshot is not None:
        return RouteDeletionBlockCode.COMPLETED_ROUTE
    return None


async def delete_route_scope(
    session: AsyncSession, target_id: UUID, *, individual: bool
) -> bool:
    try:
        group, routes = await get_deletion_scope(
            session, target_id, individual=individual, lock=True
        )
        if group is None:
            return False
        blocked = await get_deletion_block_code(
            session, group, [route.route_id for route in routes]
        )
        if blocked:
            raise HTTPException(status_code=409, detail=BLOCK_MESSAGES[blocked])
        await session.delete(routes[0] if individual else group)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    return True


async def get_route_deletion_impact(
    session: AsyncSession, target_id: UUID, *, individual: bool
) -> RouteDeletionImpact:
    group, routes = await get_deletion_scope(session, target_id, individual=individual)
    if group is None:
        raise HTTPException(status_code=404, detail="Route or route group not found.")

    route_ids = [route.route_id for route in routes]
    target_stops = col(RouteStop.route_id).in_(route_ids)
    remaining_stop = aliased(RouteStop)
    has_remaining_route = (
        select(remaining_stop.route_id)
        .join(Route, col(remaining_stop.route_id) == col(Route.route_id))
        .join(RouteGroup, col(Route.route_group_id) == col(RouteGroup.route_group_id))
        .where(
            RouteGroup.drive_date == group.drive_date,
            col(remaining_stop.route_id).not_in(route_ids),
            col(remaining_stop.location_id) == col(RouteStop.location_id),
        )
        .exists()
    )
    num_stops = await session.scalar(
        select(func.count()).select_from(RouteStop).where(target_stops)
    )
    num_unrouted = await session.scalar(
        select(func.count(col(RouteStop.location_id).distinct())).where(
            target_stops, ~has_remaining_route
        )
    )
    blocked = await get_deletion_block_code(session, group, route_ids)
    return RouteDeletionImpact(
        name=routes[0].name if individual else group.name,
        drive_date=group.drive_date,
        num_routes=len(routes),
        num_stops=num_stops or 0,
        num_drivers=len(
            {route.driver_id for route in routes if route.driver_id is not None}
        ),
        num_unrouted_locations=num_unrouted or 0,
        blocked_reason=BLOCK_MESSAGES.get(blocked) if blocked else None,
        blocked_code=blocked,
    )

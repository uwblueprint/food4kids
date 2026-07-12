"""Route freeze scheduled job.

Runs nightly at 23:59. For every route that is DUE (its group's drive_date
is today or earlier) and not yet frozen, create the RouteSnapshot +
RouteStopSnapshot rows that lock in what was delivered. The presence of the
snapshot is the freeze signal — there is no separate flag column.

The job writes NO mileage: driver history is derived at read time from
frozen routes (SUM(Route.length) grouped by driver and drive_date month)
plus manual adjustments — see DriverHistoryService. Freezing a route is what
makes it count.

Because the scan is "due and un-frozen" rather than "dated today", a missed
run (server down at 23:59), a crash mid-run, or a night with unconfigured
warehouse coordinates self-heals on the next successful run: whatever wasn't
frozen is still due. Each route is processed in its own session/transaction,
so one failing route can't poison the rest of the run.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from app.dependencies.services import get_logger
from app.models import async_session_maker_instance
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_snapshot import RouteSnapshot
from app.models.route_stop import RouteStop
from app.models.route_stop_snapshot import RouteStopSnapshot
from app.models.system_settings import SystemSettings


async def _freeze_route(
    maker: async_sessionmaker[AsyncSession],
    route_id: UUID,
    warehouse_address: str,
    warehouse_latitude: float,
    warehouse_longitude: float,
) -> None:
    """Freeze one route atomically in a fresh session.

    Raises on failure (nothing is committed in that case — the route stays
    due for the next run)."""
    logger = get_logger()
    async with maker() as session:
        result = await session.execute(
            select(Route)
            .where(Route.route_id == route_id)
            .options(
                selectinload(Route.snapshot),  # type: ignore[arg-type]
                selectinload(Route.route_stops).selectinload(  # type: ignore[arg-type]
                    RouteStop.location  # type: ignore[arg-type]
                ),
                selectinload(Route.route_stops).selectinload(  # type: ignore[arg-type]
                    RouteStop.snapshot  # type: ignore[arg-type]
                ),
            )
        )
        route = result.scalars().first()
        if route is None or route.snapshot is not None:
            # Deleted or frozen since the scan — nothing to do.
            return

        session.add(
            RouteSnapshot(
                route_id=route.route_id,
                start_address=warehouse_address,
                start_latitude=warehouse_latitude,
                start_longitude=warehouse_longitude,
            )
        )

        for stop in route.route_stops:
            if stop.snapshot is not None:
                continue
            loc = stop.location
            if loc.latitude is None or loc.longitude is None:
                logger.warning(
                    f"Location {loc.location_id} missing coordinates; "
                    f"skipping snapshot for stop {stop.route_stop_id}."
                )
                continue
            session.add(
                RouteStopSnapshot(
                    route_stop_id=stop.route_stop_id,
                    address=loc.address,
                    contact_name=loc.contact_name,
                    phone_primary=loc.phone_primary,
                    phone_secondary=loc.phone_secondary,
                    num_children=loc.num_children,
                    notes=loc.notes,
                    latitude=loc.latitude,
                    longitude=loc.longitude,
                )
            )

        # One commit: the route snapshot and its stop snapshots land
        # together or not at all.
        await session.commit()


async def process_daily_driver_history() -> None:
    """Freeze all due, un-frozen routes.

    Runs at 11:59 PM every day; safe to re-run at any time (idempotent)."""
    logger = get_logger()

    if async_session_maker_instance is None:
        logger.error("Database session maker not initialized")
        return

    today = date.today()
    end_of_today = datetime.combine(today, datetime.max.time())

    try:
        # --------------------------------------------------------------
        # 1. Scan for due, un-frozen routes — plain IDs only, since each
        #    route is processed in its own session. Includes past dates,
        #    not just today: routes missed by a downed or crashed run
        #    stay due until a run succeeds.
        # --------------------------------------------------------------
        async with async_session_maker_instance() as session:
            scan = await session.execute(
                select(Route.route_id, RouteGroup.drive_date)
                .join(RouteGroup, RouteGroup.route_group_id == Route.route_group_id)  # type: ignore[arg-type]
                .outerjoin(RouteSnapshot, RouteSnapshot.route_id == Route.route_id)  # type: ignore[arg-type]
                .where(RouteGroup.drive_date <= end_of_today)
                .where(col(RouteSnapshot.route_id).is_(None))
                .order_by(col(RouteGroup.drive_date))
            )
            due: list[tuple[UUID, date]] = [
                (route_id, drive_date.date()) for route_id, drive_date in scan.all()
            ]

            if not due:
                logger.info("No due un-frozen routes; nothing to do.")
                return

            backlog = sum(1 for _, dd in due if dd < today)
            if backlog:
                logger.warning(
                    f"Catch-up: {backlog} of {len(due)} due routes are from "
                    f"past dates (missed or previously-skipped runs)."
                )

            # ----------------------------------------------------------
            # 2. Warehouse coordinates are required to freeze. If they're
            #    missing, freeze nothing — loudly. The routes stay due,
            #    so this self-heals on the first run after they're set.
            # ----------------------------------------------------------
            settings_result = await session.execute(select(SystemSettings).limit(1))
            system_settings = settings_result.scalars().first()

            if (
                system_settings is None
                or not system_settings.warehouse_location
                or system_settings.warehouse_latitude is None
                or system_settings.warehouse_longitude is None
            ):
                logger.error(
                    f"Warehouse coordinates not configured — cannot freeze "
                    f"{len(due)} due routes (their mileage won't count until "
                    f"frozen). They remain due and will be processed on the "
                    f"next run after coordinates are set."
                )
                return

            warehouse_address = system_settings.warehouse_location
            warehouse_latitude = system_settings.warehouse_latitude
            warehouse_longitude = system_settings.warehouse_longitude

        # --------------------------------------------------------------
        # 3. Freeze, one fresh session/transaction per route. A failing
        #    route is logged and skipped without poisoning the run.
        # --------------------------------------------------------------
        frozen_count = 0
        failed_count = 0
        for route_id, drive_date in due:
            try:
                await _freeze_route(
                    async_session_maker_instance,
                    route_id,
                    warehouse_address,
                    warehouse_latitude,
                    warehouse_longitude,
                )
                frozen_count += 1
            except Exception:
                failed_count += 1
                logger.exception(
                    f"Failed to freeze route {route_id} (drive_date "
                    f"{drive_date}); it remains due and will be retried on "
                    f"the next run."
                )

        logger.info(f"Froze {frozen_count} routes ({failed_count} failures).")

    except Exception as error:
        logger.error(
            f"Failed to process daily driver history: {error!s}", exc_info=True
        )
        raise error

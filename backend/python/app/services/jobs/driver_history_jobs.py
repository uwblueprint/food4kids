"""Driver history scheduled jobs.

Runs nightly at 23:59. Two jobs in one:

1. **Freeze today's routes.** For every route whose drive_date is today,
   create the RouteSnapshot + RouteStopSnapshot rows that lock in what was
   delivered. The presence of the snapshot is the freeze signal — there is
   no separate flag column. Idempotent: skip routes that already have a
   RouteSnapshot (e.g. if the job is re-run after a crash).

2. **Mileage aggregation.** Sum each driver's route lengths and update
   DriverHistory — but only for the routes frozen *in this run*, so a
   re-run never double-counts a driver's km (the freeze in step 1 is the
   idempotency gate for both steps).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from app.dependencies.services import get_logger
from app.models import async_session_maker_instance
from app.models.driver_history import DriverHistory
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.route_snapshot import RouteSnapshot
from app.models.route_stop import RouteStop
from app.models.route_stop_snapshot import RouteStopSnapshot
from app.models.system_settings import SystemSettings


async def process_daily_driver_history() -> None:
    """Process driver history for the day - runs at 11:59 PM every day."""
    logger = get_logger()

    if async_session_maker_instance is None:
        logger.error("Database session maker not initialized")
        return

    today = date.today()
    current_year = today.year
    current_month = today.month
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())

    try:
        async with async_session_maker_instance() as session:
            # ----------------------------------------------------------
            # 1. Find today's routes (joined to their groups for the date
            #    filter). Eager-load stops + their locations + existing
            #    snapshots so the freeze loop below doesn't issue lazy
            #    queries inside the async context.
            # ----------------------------------------------------------
            routes_statement = (
                select(Route)
                .join(RouteGroup, RouteGroup.route_group_id == Route.route_group_id)  # type: ignore[arg-type]
                .where(
                    and_(
                        RouteGroup.drive_date >= start_of_day,  # type: ignore[arg-type]
                        RouteGroup.drive_date <= end_of_day,  # type: ignore[arg-type]
                    )
                )
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
            routes_result = await session.execute(routes_statement)
            todays_routes = list(routes_result.scalars().all())

            if not todays_routes:
                logger.info("No routes scheduled for today")
                return

            # ----------------------------------------------------------
            # 2. Snapshot freeze. One RouteSnapshot per route (using
            #    current warehouse coords from SystemSettings) + one
            #    RouteStopSnapshot per stop (from the live Location).
            # ----------------------------------------------------------
            settings_result = await session.execute(select(SystemSettings).limit(1))
            system_settings = settings_result.scalars().first()

            warehouse_ready = (
                system_settings is not None
                and system_settings.warehouse_location
                and system_settings.warehouse_latitude is not None
                and system_settings.warehouse_longitude is not None
            )
            if not warehouse_ready:
                logger.warning(
                    "Warehouse coordinates not configured — skipping snapshot "
                    "creation. Routes will not be frozen for today's drive_date."
                )

            snapshots_created = 0
            stop_snapshots_created = 0
            # Routes frozen in THIS run — only these get their mileage
            # aggregated below, so re-running the job can't double-count.
            newly_frozen: list[Route] = []
            for route in todays_routes:
                if route.snapshot is not None:
                    # Already frozen on a prior run (mileage counted then);
                    # idempotent skip.
                    continue
                if not warehouse_ready:
                    continue

                assert system_settings is not None
                assert system_settings.warehouse_location is not None
                assert system_settings.warehouse_latitude is not None
                assert system_settings.warehouse_longitude is not None

                route_snap = RouteSnapshot(
                    route_id=route.route_id,
                    start_address=system_settings.warehouse_location,
                    start_latitude=system_settings.warehouse_latitude,
                    start_longitude=system_settings.warehouse_longitude,
                )
                session.add(route_snap)
                snapshots_created += 1
                newly_frozen.append(route)

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
                    stop_snap = RouteStopSnapshot(
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
                    session.add(stop_snap)
                    stop_snapshots_created += 1

            # Commit snapshots before mileage aggregation so a partial failure
            # doesn't roll back the freeze along with the aggregation.
            await session.commit()
            if snapshots_created:
                logger.info(
                    f"Froze {snapshots_created} routes "
                    f"({stop_snapshots_created} stop snapshots)"
                )

            # ----------------------------------------------------------
            # 3. Mileage aggregation: only routes frozen in this run (so a
            #    re-run never double-counts), grouped by Route.driver_id.
            # ----------------------------------------------------------
            assigned = [r for r in newly_frozen if r.driver_id is not None]
            if not assigned:
                logger.info("No newly-frozen assigned routes; nothing to aggregate.")
                return

            driver_distances: dict[UUID, float] = {}
            for route in assigned:
                assert route.driver_id is not None  # narrowed above
                driver_distances[route.driver_id] = (
                    driver_distances.get(route.driver_id, 0.0) + route.length
                )

            for driver_id, total_distance in driver_distances.items():
                existing_history = (
                    (
                        await session.execute(
                            select(DriverHistory).where(
                                and_(
                                    col(DriverHistory.driver_id) == driver_id,
                                    col(DriverHistory.year) == current_year,
                                    col(DriverHistory.month) == current_month,
                                )
                            )
                        )
                    )
                    .scalars()
                    .first()
                )

                if existing_history:
                    existing_history.km += total_distance
                    logger.info(
                        f"Updated driver history for driver {driver_id}: "
                        f"added {total_distance} km (new total: {existing_history.km} km)"
                    )
                else:
                    new_history = DriverHistory(
                        driver_id=driver_id,
                        year=current_year,
                        month=current_month,
                        km=total_distance,
                    )
                    session.add(new_history)
                    logger.info(
                        f"Created driver history for driver {driver_id}: "
                        f"{total_distance} km for year {current_year}"
                    )

            await session.commit()
            logger.info(
                f"Successfully aggregated {len(assigned)} routes "
                f"for {len(driver_distances)} drivers"
            )

    except Exception as error:
        logger.error(
            f"Failed to process daily driver history: {error!s}", exc_info=True
        )
        raise error

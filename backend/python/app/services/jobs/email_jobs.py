"""Scheduled email sending jobs

This module contains all cron-scheduled email jobs that run at specific times.
Jobs use the unified EmailDispatcher to render and send emails.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import and_
from sqlmodel import select

if TYPE_CHECKING:
    from sqlalchemy.sql.schema import Table

from app.dependencies.services import get_email_dispatcher, get_logger
from app.models.driver import Driver
from app.models.route import Route
from app.models.route_group import RouteGroup
from app.models.user import User


async def send_route_reminders() -> None:
    """Scheduled job: Send route reminders to drivers for tomorrow's routes.

    Runs daily (typically at 7:00 AM) and sends reminder emails to all drivers
    assigned to routes the next day.

    This job:
    - Queries all driver assignments for tomorrow
    - For each driver, renders and sends a route reminder email
    - Logs successes and failures individually
    - Continues sending even if one email fails
    """

    from app.models import async_session_maker_instance

    logger = get_logger()
    dispatcher = get_email_dispatcher()

    if async_session_maker_instance is None:
        logger.error("Database session maker not initialized")
        return

    tomorrow = date.today() + timedelta(days=1)
    start_of_day = datetime.combine(tomorrow, datetime.min.time())
    end_of_day = datetime.combine(tomorrow, datetime.max.time())

    try:
        async with async_session_maker_instance() as session:
            # Get all drivers assigned to routes tomorrow
            # Cast model tables to SQLAlchemy Table objects so mypy can reason
            # about column expressions.
            # Cast the model classes to Any before accessing `__table__` so
            # mypy does not complain about missing attributes on the class
            # objects.
            Route_table = cast("Table", cast("Any", Route).__table__)
            Driver_table = cast("Table", cast("Any", Driver).__table__)
            User_table = cast("Table", cast("Any", User).__table__)
            RouteGroup_table = cast("Table", cast("Any", RouteGroup).__table__)

            # Select full models so typing is recognized by mypy; use table
            # columns for SQL expressions.
            statement = (
                select(Route, User, RouteGroup)
                .join(Driver, Route_table.c.driver_id == Driver_table.c.driver_id)
                .join(User, Driver_table.c.user_id == User_table.c.user_id)
                .join(
                    RouteGroup,
                    Route_table.c.route_group_id == RouteGroup_table.c.route_group_id,
                )
                .where(
                    and_(
                        RouteGroup_table.c.drive_date >= start_of_day,
                        RouteGroup_table.c.drive_date <= end_of_day,
                        Route_table.c.driver_id.isnot(None),
                    )
                )
                .order_by(User_table.c.email)
            )

            result = await session.execute(statement)
            upcoming_routes = result.all()

            if not upcoming_routes:
                logger.info("No upcoming routes found for tomorrow, skipping reminders")
                return

            sent_count = 0
            failed_count = 0

            # Send reminder email to each driver
            for route, user, route_group in upcoming_routes:
                recipient_email = user.email
                driver_name = user.full_name
                # Combine drive_date (date) with route start_time (time) if present
                if route.start_time:
                    route_date = datetime.combine(
                        route_group.drive_date.date(), route.start_time
                    )
                else:
                    route_date = route_group.drive_date
                route_distance = route.length

                # Format date, time, and distance for email
                date_only = route_date.date().strftime("%A, %B %d, %Y")
                time_only = route_date.time().strftime("%I:%M %p")
                rounded_distance = str(round(route_distance))

                # Prepare context matching `view-upcoming-route` template placeholders
                context = {
                    "Driver_Name_To_Replace": driver_name,
                    "Date_To_Replace": date_only,
                    "Time_To_Replace": time_only,
                    "Route_Duration_To_Replace": rounded_distance,
                    "Upcoming_Route_URL": "https://app.example.com/routes",  # Note: update to actual route URL!
                }

                try:
                    await dispatcher.dispatch(
                        email_type="view-upcoming-route",
                        to=recipient_email,
                        context=context,
                    )
                    sent_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"Failed to send route reminder to {recipient_email}: {e!s}",
                        exc_info=True,
                    )
                    # Continue sending to other drivers even if one fails

            logger.info(
                f"Route reminder job completed: sent {sent_count}, failed {failed_count}"
            )

    except Exception as error:
        logger.error(
            f"Failed to process route reminder emails: {error!s}",
            exc_info=True,
        )
        raise error

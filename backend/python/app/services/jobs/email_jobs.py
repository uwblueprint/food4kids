"""Scheduled email sending jobs

This module contains all cron-scheduled email jobs that run at specific times.
Jobs use the unified EmailDispatcher to render and send emails.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import and_
from sqlmodel import col, select

from app.dependencies.services import get_email_dispatcher, get_logger
from app.models.driver import Driver
from app.models.route import ASSIGNED_ROUTE_HAS_START_TIME_CONSTRAINT, Route
from app.models.route_group import RouteGroup
from app.models.user import User

# Placeholder until there is a deployment to link at. The template still needs
# some value for Upcoming_Route_URL, and dispatch would raise without it.
UPCOMING_ROUTE_URL = "https://app.example.com/routes"


async def send_route_reminders(reminder_days: list[int]) -> None:
    """Scheduled job: email drivers about routes ``reminder_days`` days out.

    The scheduler registers one instance of this job per distinct reminder time
    (see ``refresh_daily_reminder_email_schedule``), passing the lead days
    configured for that time. A lead day of 0 means routes driving today.

    Renders through the EmailDispatcher, which substitutes the template's
    Jinja2 placeholders. Sends are attempted for every driver; a failure is
    logged and the remaining drivers are still emailed.
    """

    from app.models import async_session_maker_instance

    logger = get_logger()

    if not reminder_days:
        logger.info("No reminder lead days configured, skipping emails")
        return

    if async_session_maker_instance is None:
        logger.error("Database session maker not initialized")
        return

    dispatcher = get_email_dispatcher()

    try:
        async with async_session_maker_instance() as session:
            target_dates = {date.today() + timedelta(days=day) for day in reminder_days}

            # Narrow in SQL to the span the lead days cover, then match the exact
            # dates below. The span is only a prefilter: non-contiguous lead days
            # (say 1 and 3) cover a range that also contains days nobody asked for.
            start_of_span = min(target_dates)
            end_of_span = max(target_dates)

            statement = (
                select(Route, User, RouteGroup)
                .join(RouteGroup, RouteGroup.route_group_id == Route.route_group_id)  # type: ignore[arg-type]
                .join(Driver, Driver.driver_id == Route.driver_id)  # type: ignore[arg-type]
                .join(User, User.user_id == Driver.user_id)  # type: ignore[arg-type]
                .where(
                    and_(
                        RouteGroup.drive_date >= start_of_span,  # type: ignore[arg-type]
                        RouteGroup.drive_date <= end_of_span,  # type: ignore[arg-type]
                        col(Route.driver_id).isnot(None),
                    )
                )
                .order_by(User.email)
            )

            result = await session.execute(statement)
            upcoming_routes = [
                row for row in result.all() if row.RouteGroup.drive_date in target_dates
            ]

            if not upcoming_routes:
                logger.info(
                    "No upcoming routes found for configured reminder days, "
                    "skipping emails"
                )
                return

            # One lookup for the run, not one per driver.
            org_contact = await dispatcher.org_contact_context()
            sent_count = 0
            failed_count = 0

            for route, user, route_group in upcoming_routes:
                try:
                    # drive_date is date-only, so start_time is the only clock
                    # time. Every route here is assigned, and an assigned route
                    # is guaranteed a start_time by a CHECK constraint -- so a
                    # null one means the database drifted from its own schema,
                    # and inventing a time would hide that.
                    if route.start_time is None:
                        raise ValueError(
                            f"Route {route.route_id} is assigned to a driver but "
                            f"has no start_time, violating "
                            f"{ASSIGNED_ROUTE_HAS_START_TIME_CONSTRAINT}"
                        )

                    await dispatcher.dispatch(
                        email_type="view-upcoming-route",
                        to=user.email,
                        org_contact=org_contact,
                        context={
                            "Driver_Name_To_Replace": user.full_name,
                            "Date_To_Replace": route_group.drive_date.strftime(
                                "%A, %B %d, %Y"
                            ),
                            "Time_To_Replace": route.start_time.strftime("%I:%M %p"),
                            "Route_Duration_To_Replace": str(round(route.length)),
                            "Upcoming_Route_URL": UPCOMING_ROUTE_URL,
                        },
                    )
                    sent_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"Failed to send route reminder to {user.email}: {e!s}",
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

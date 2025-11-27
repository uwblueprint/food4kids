"""Email reminder cheduled jobs"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import and_
from sqlmodel import select

from app.config import settings
from app.dependencies.services import get_logger
from app.models.driver import Driver
from app.models.driver_assignment import DriverAssignment
from app.models.route import Route
from app.services.implementations.email_service import EmailService


async def process_daily_reminder_emails() -> None:
    """Sends out daily reminder emails for the day - runs at 7:00 AM every day

    This job:
    - Finds all drivers who are assigned to routes tomorrow
    """

    from app.models import (
        async_session_maker_instance,  # Placed here to ensure testing file functions as normal
    )

    logger = get_logger()

    if async_session_maker_instance is None:
        logger.error("Database session maker not initialized")
        return

    tomorrow = date.today() + timedelta(days=1)
    start_of_day = datetime.combine(tomorrow, datetime.min.time())
    end_of_day = datetime.combine(tomorrow, datetime.max.time())
    logger.info(f"{start_of_day}, {end_of_day}")
    try:
        async with async_session_maker_instance() as session:
            # Get all drivers assigned to routes tomorrow
            statement = (
                select(
                    Driver.email,
                    DriverAssignment.time,
                    Route.length,
                )
                .join(Route, DriverAssignment.route_id == Route.route_id)  # type: ignore[arg-type]
                .join(Driver, DriverAssignment.driver_id == Driver.driver_id)  # type: ignore[arg-type]
                .where(
                    and_(
                        Driver.email is not None,  # type: ignore[arg-type]
                        DriverAssignment.time >= start_of_day,  # type: ignore[arg-type]
                        DriverAssignment.time <= end_of_day,  # type: ignore[arg-type]
                        DriverAssignment.completed.is_(False),  # type: ignore[attr-defined]
                    )
                )
                .order_by(Driver.email)
            )

            result = await session.execute(statement)
            upcoming_routes = result.all()
            logger.info(f"Successfully retrieved upcoming routes: {upcoming_routes}")

            if not upcoming_routes:
                logger.info("No Upcoming Routes found for today, skipping emails")
                return

            email_service = EmailService(
                logger,
                {
                    "refresh_token": settings.mailer_refresh_token,
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_id": settings.mailer_client_id,
                    "client_secret": settings.mailer_client_secret,
                },
                settings.mailer_user,
                "Food4Kids",
            )

            for row in upcoming_routes:
                recipient_email = row.email
                route_date: datetime = row.time
                route_distance = row.length

                date_only = route_date.date().strftime("%A, %B %d, %Y")
                time_only = route_date.time().strftime("%I:%M %p")
                rounded_distance = str(round(route_distance))

                with open("./app/templates/route_reminder.html") as file:
                    formatted_email = file.read()

                formatted_email = formatted_email.replace("Date_To_Replace", date_only)
                formatted_email = formatted_email.replace("Time_To_Replace", time_only)
                formatted_email = formatted_email.replace(
                    "Length_To_Replace", rounded_distance
                )
                logger.info(f"Sent Email to {recipient_email}")
                email_service.send_email(
                    to=recipient_email,
                    subject="Upcoming Route Reminder",
                    body=formatted_email,
                )

            logger.info("Successfully sent reminder emails")

    except Exception as error:
        logger.error(
            f"Failed to process daily reminder emails: {error!s}", exc_info=True
        )
        raise error

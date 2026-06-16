"""Scheduled jobs - follows same pattern as routers"""

from __future__ import annotations

from datetime import time
from typing import TYPE_CHECKING

from sqlmodel import select

from app.models.system_settings import SystemSettings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.services.implementations.scheduler_service import SchedulerService

DEFAULT_DAILY_REMINDER_TIME = time(9, 0)
DAILY_REMINDER_JOB_ID = "daily_reminder_emails"


def _schedule_daily_reminder_emails(
    scheduler_service: SchedulerService, reminder_time: time
) -> None:
    from .email_reminder_jobs import process_daily_reminder_emails

    scheduler_service.remove_job(DAILY_REMINDER_JOB_ID)
    scheduler_service.add_cron_job(
        process_daily_reminder_emails,
        job_id=DAILY_REMINDER_JOB_ID,
        hour=reminder_time.hour,
        minute=reminder_time.minute,
    )


async def refresh_daily_reminder_email_schedule(
    scheduler_service: SchedulerService, session: AsyncSession
) -> None:
    """Reschedule the reminder job from the persisted system settings."""
    if getattr(scheduler_service, "scheduler", None) is None:
        return

    result = await session.execute(select(SystemSettings).limit(1))
    system_settings = result.scalars().first()
    reminder_time = (
        system_settings.email_reminder_time
        if system_settings is not None
        else DEFAULT_DAILY_REMINDER_TIME
    )
    _schedule_daily_reminder_emails(scheduler_service, reminder_time)


async def init_jobs(scheduler_service: SchedulerService, session: AsyncSession) -> None:
    """Initialize all scheduled jobs - add new jobs here

    This function follows the same pattern as app.routers.init_app().
    To add a new scheduled job:
    1. Create a new file in this directory (e.g., email_jobs.py)
    2. Define your job function
    3. Import and register it here
    """
    from .driver_history_jobs import process_daily_driver_history

    # Driver history mark daily routes as complete
    scheduler_service.add_cron_job(
        process_daily_driver_history,
        job_id="daily_driver_history",
        hour=23,
        minute=59,
    )

    await refresh_daily_reminder_email_schedule(scheduler_service, session)

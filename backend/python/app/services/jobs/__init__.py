"""Scheduled jobs - follows same pattern as routers"""

from app.services.implementations.scheduler_service import SchedulerService


def init_jobs(scheduler_service: SchedulerService) -> None:
    """Initialize all scheduled jobs - add new jobs here

    This function follows the same pattern as app.routers.init_app().
    To add a new scheduled job:
    1. Create a new file in this directory (e.g., email_jobs.py)
    2. Define your job function
    3. Import and register it here
    """
    from .driver_history_jobs import process_daily_driver_history
    from .email_reminder_jobs import process_daily_reminder_emails
    from .geocoding_refresh_jobs import refresh_geocoding

    # Driver history mark daily routes as complete
    scheduler_service.add_cron_job(
        process_daily_driver_history,
        job_id="daily_driver_history",
        hour=23,
        minute=59,
    )

    # Email reminders - runs daily at 12 PM
    scheduler_service.add_cron_job(
        process_daily_reminder_emails,
        job_id="daily_reminder_emails",
        hour=12,
        minute=0,
    )

    # Geocoding refresh - runs daily at 2 AM
    scheduler_service.add_cron_job(
        refresh_geocoding,
        job_id="daily_geocoding_refresh",
        hour=2,
        minute=0,
    )

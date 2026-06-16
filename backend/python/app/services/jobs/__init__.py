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
    from .email_jobs import send_route_reminders

    # Driver history mark daily routes as complete
    scheduler_service.add_cron_job(
        process_daily_driver_history,
        job_id="daily_driver_history",
        hour=23,
        minute=59,
    )

    # For now, runs daily at 7 AM... (may need to change in future!)
    scheduler_service.add_cron_job(
        send_route_reminders,
        job_id="route_reminders",
        hour=7,
        minute=0,
    )

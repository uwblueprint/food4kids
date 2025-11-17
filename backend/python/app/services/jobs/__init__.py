"""Scheduled jobs - follows same pattern as routers"""


def init_jobs(scheduler_service) -> None:
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

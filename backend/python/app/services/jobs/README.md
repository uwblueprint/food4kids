# Scheduled Jobs

This directory contains all scheduled tasks (cron jobs) for the Food4Kids platform.

### Architecture

```
app/
  services/
    implementations/
      scheduler_service.py    # Central scheduler management
    jobs/
      __init__.py            # init_jobs() - registers all jobs
      driver_history_jobs.py # Example job implementation
      README.md              # This file
```

### How It Works

1. On application startup, `SchedulerService` is initialized and started
2. `init_jobs()` is called, which imports all job modules and registers them with the scheduler
3. APScheduler runs jobs in background threads according to their cron schedules
4. Async job functions are automatically wrapped to run in their own event loops
5. On application shutdown, the scheduler is gracefully stopped

## Creating Your Own Cron Job

Follow these steps to add a new scheduled job:

### Step 1: Create a Job File

Create a new file in this directory (e.g., `email_jobs.py`, `cleanup_jobs.py`):

```python
"""Your job description"""
import logging
from app.dependencies.services import get_logger
from app.models import async_session_maker_instance


async def your_job_function() -> None:
    """Description of what this job does
    """
    logger = get_logger()
    
    if async_session_maker_instance is None:
        logger.error("Database session maker not initialized")
        return
    
    try:
        async with async_session_maker_instance() as session:
            # Your job logic here
            await session.commit()
            logger.info("Job completed successfully")
    except Exception as e:
        logger.error(f"Error in job: {e}", exc_info=True)
        if async_session_maker_instance:
            try:
                async with async_session_maker_instance() as session:
                    await session.rollback()
            except Exception:
                pass
        raise
```

### Step 2: Register the Job

Add your job to `__init__.py`:

```python
def init_jobs(scheduler_service) -> None:
    from .driver_history_jobs import process_daily_driver_history
    from .email_jobs import your_job_function  # Import your new job
    
    # Existing jobs...
    scheduler_service.add_cron_job(
        process_daily_driver_history,
        job_id="daily_driver_history",
        hour=23,
        minute=59,
    )
    
    # Register your new job
    scheduler_service.add_cron_job(
        your_job_function,
        job_id="your_job_id",
        hour=9,
        minute=0,
        day_of_week=0,
    )
```

### Step 3: Cron Schedule Parameters

The `add_cron_job()` method accepts these parameters:

- `job_id` (required): Unique identifier for the job
- `hour` (default: "*"): Hour (0-23) or "*" for every hour
- `minute` (default: "*"): Minute (0-59) or "*" for every minute
- `day_of_week` (default: "*"): Day of week (0-6, 0=Monday) or "*" for every day
- `day` (default: "*"): Day of month (1-31) or "*" for every day
- `month` (default: "*"): Month (1-12) or "*" for every month

### Testing

To test your job manually, you can call it directly using a test file:

```python
import asyncio
import logging

from app.models import init_app

from app.services.jobs.email_reminder_jobs import your_job

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    init_app()
    asyncio.run(your_job())

```

You can also create a test endpoint in development to trigger jobs manually.


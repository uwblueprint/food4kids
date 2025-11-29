# Job Worker Documentation

## Overview

The Job Worker is a background process that processes jobs from a database queue. Unlike traditional queue systems (Redis/Celery), **the database table itself acts as the queue**. Jobs are stored as rows in the `jobs` table, and the `progress` column tracks their state.

## Key Features

- **Database as Queue**: No separate queue system needed - jobs persist in PostgreSQL
- **Survives Restarts**: Jobs persist in database, so worker can resume after crashes
- **Orphan Recovery**: Automatically resets stuck jobs on startup
- **Timeout Protection**: Jobs that run too long are automatically marked as FAILED
- **Race Condition Prevention**: Uses `SELECT FOR UPDATE SKIP LOCKED` to prevent duplicate processing
- **Resilient**: Worker continues running even if individual jobs fail

## Architecture

### The Loop

The worker continuously polls the database for `QUEUED` jobs and processes them:

```
Client → API → Database (PENDING → QUEUED) → Worker Loop → Database (RUNNING → COMPLETED)
```

### Job States

Jobs flow through these states:

1. **PENDING**: Job created by API, not yet ready for processing
2. **QUEUED**: Job is ready for worker to pick up (moved here by `enqueue()`)
3. **RUNNING**: Worker is actively processing the job
4. **COMPLETED**: Job finished successfully
5. **FAILED**: Job encountered an error or timed out

### Database Schema

The `jobs` table tracks:
- `job_id`: Unique identifier (UUID)
- `progress`: Current state (enum: PENDING, QUEUED, RUNNING, COMPLETED, FAILED)
- `created_at`: When job was created
- `started_at`: When job started processing (set when moving to RUNNING)
- `finished_at`: When job completed or failed
- `updated_at`: Last update timestamp
- `route_group_id`: Optional reference to route group

## How It Works

### 1. Worker Startup

When the application starts, the worker:
- Initializes with configurable settings (poll interval, timeout, etc.)
- Runs orphan recovery to reset any jobs stuck in RUNNING state
- Starts the main polling loop

### 2. Main Loop

The worker continuously:
1. Checks for stuck jobs (jobs running longer than timeout)
2. Polls database for next QUEUED job (oldest first, FIFO)
3. Processes the job if found
4. Waits `poll_interval` seconds before checking again

### 3. Processing a Job

When a job is found:

1. **Lock Job**: Uses `SELECT FOR UPDATE SKIP LOCKED` to prevent race conditions
2. **Mark as RUNNING**: Updates job status and sets `started_at` timestamp
3. **Execute Work**: Calls `generate_routes()` with timeout protection
4. **Mark as COMPLETED**: Updates job status and sets `finished_at` timestamp
5. **Error Handling**: If any step fails, job is marked as FAILED

### 4. Orphan Recovery

On startup, the worker finds all jobs in `RUNNING` state and resets them to `QUEUED`. This handles cases where:
- The application crashed while processing a job
- The worker was stopped mid-processing
- The database connection was lost

### 5. Stuck Job Detection

Periodically, the worker checks for jobs that have been `RUNNING` longer than the timeout (default: 30 minutes). These are automatically marked as `FAILED` to prevent infinite processing.

## Configuration

The worker is configured in `app/__init__.py`:

```python
job_worker = JobWorker(
    poll_interval=5,
    job_timeout_minutes=30,
    enable_orphan_recovery=True
)
```

### Parameters

- **poll_interval** (int): Seconds between checking for new jobs (default: 5)
- **job_timeout_minutes** (int): Maximum time a job can run before being marked as FAILED (default: 30)
- **enable_orphan_recovery** (bool): Whether to reset orphaned RUNNING jobs on startup (default: True)

## Testing

### Manual Testing via Database

1. **Create a test job**:
```bash
docker-compose exec db psql -U postgres -d f4k -c \
  "INSERT INTO jobs (job_id, progress, created_at) \
   VALUES (gen_random_uuid(), 'QUEUED', NOW()) \
   RETURNING job_id;"
```

2. **Monitor the worker logs**:
```bash
docker-compose logs -f backend | grep -i "worker\|job"
```

3. **Check job status**:
```bash
# Check all jobs
docker-compose exec db psql -U postgres -d f4k -c \
  "SELECT job_id, progress, started_at, finished_at \
   FROM jobs ORDER BY created_at DESC LIMIT 5;"

# Check specific job
docker-compose exec db psql -U postgres -d f4k -c \
  "SELECT * FROM jobs WHERE job_id = 'YOUR_JOB_ID';"
```

4. **Verify completion**:
```bash
# Wait ~15 seconds (10s sleep in generate_routes + processing time)
docker-compose exec db psql -U postgres -d f4k -c \
  "SELECT job_id, progress, started_at, finished_at, \
   EXTRACT(EPOCH FROM (finished_at - started_at)) as duration_seconds \
   FROM jobs WHERE progress = 'COMPLETED' \
   ORDER BY finished_at DESC LIMIT 1;"
```

### Testing via API

1. **Create and enqueue a job**:
```bash
curl -X POST "http://localhost:8080/jobs/generate" \
  -H "Content-Type: application/json" \
  -d '{"location_group": {...}, "settings": {...}}'
```

2. **Check job status**:
```bash
curl "http://localhost:8080/jobs/{job_id}"
```

### Expected Behavior

A successful job should:
- Start as `QUEUED`
- Move to `RUNNING` within ~5 seconds (poll interval)
- Execute `generate_routes()` (currently simulates 10 seconds of work)
- Complete as `COMPLETED` with proper timestamps
- Show logs: "Found job...", "Starting job...", "Generating routes...", "completed successfully"

## Monitoring

### Check Worker Status

```bash
# See if worker is running and polling
docker-compose logs backend --tail=50 | grep "Worker loop\|QUEUED"

# Check for errors
docker-compose logs backend --tail=100 | grep -i "error\|exception\|failed"
```

### Check Job Statistics

```bash
# Count jobs by status
docker-compose exec db psql -U postgres -d f4k -c \
  "SELECT progress, COUNT(*) as count \
   FROM jobs GROUP BY progress;"

# Find stuck jobs
docker-compose exec db psql -U postgres -d f4k -c \
  "SELECT job_id, progress, started_at, \
   EXTRACT(EPOCH FROM (NOW() - started_at))/60 as minutes_running \
   FROM jobs \
   WHERE progress = 'RUNNING' \
   AND started_at < NOW() - INTERVAL '30 minutes';"
```

## Implementation Details

### Session Handling

The worker uses separate database sessions for:
- Finding jobs (`process_next_job`)
- Processing jobs (`process_job`)

This ensures clean transaction boundaries and prevents session conflicts.

### Race Condition Prevention

Uses PostgreSQL's `SELECT FOR UPDATE SKIP LOCKED`:
- Locks the row when selecting
- Skips rows already locked by other workers
- Prevents multiple workers from processing the same job

### Error Handling

- Individual job failures don't crash the worker
- Failed jobs are logged and marked as `FAILED`
- Worker continues processing other jobs
- Exceptions are caught and logged at each level

## Extending the Worker

### Implementing Route Generation

The `generate_routes()` method in `job_worker.py` currently simulates work. To implement actual route generation:

```python
async def generate_routes(self, job: Job) -> None:
    """Execute the actual route generation algorithm."""
    self.logger.info(f"Job {job.job_id}: Starting route generation...")
    
    # 1. Fetch location group data
    location_group = await fetch_location_group(job.location_group_id)
    
    # 2. Run optimization algorithm
    routes = await optimize_routes(
        locations=location_group.locations,
        settings=job.settings
    )
    
    # 3. Save results
    await save_route_results(job.job_id, routes)
    
    self.logger.info(f"Job {job.job_id}: Route generation complete")
```

### Adding New Job Types

To support different job types:
1. Add a `job_type` field to the `Job` model
2. Add a switch in `generate_routes()` to handle different types
3. Or create separate worker classes for different job types

## Troubleshooting

### Jobs Not Processing

1. **Check if worker is running**:
   ```bash
   docker-compose logs backend | grep "Job worker starting"
   ```

2. **Check for QUEUED jobs**:
   ```bash
   docker-compose exec db psql -U postgres -d f4k -c \
     "SELECT COUNT(*) FROM jobs WHERE progress = 'QUEUED';"
   ```

3. **Check worker logs for errors**:
   ```bash
   docker-compose logs backend --tail=100 | grep -i "error\|exception"
   ```

### Jobs Stuck in RUNNING

1. **Check for orphaned jobs**:
   ```bash
   docker-compose exec db psql -U postgres -d f4k -c \
     "SELECT job_id, started_at FROM jobs WHERE progress = 'RUNNING';"
   ```

2. **Manually reset if needed**:
   ```bash
   docker-compose exec db psql -U postgres -d f4k -c \
     "UPDATE jobs SET progress = 'QUEUED', started_at = NULL \
      WHERE progress = 'RUNNING' AND job_id = 'YOUR_JOB_ID';"
   ```

3. **Worker will auto-recover on next restart** (if `enable_orphan_recovery=True`)

### Jobs Failing Immediately

1. **Check logs for error details**:
   ```bash
   docker-compose logs backend | grep -A 10 "Job.*failed"
   ```

2. **Verify enum values match**:
   ```bash
   docker-compose exec db psql -U postgres -d f4k -c \
     "SELECT unnest(enum_range(NULL::progressenum));"
   ```

3. **Check database connection**:
   ```bash
   docker-compose exec db psql -U postgres -d f4k -c "SELECT 1;"
   ```

## Related Files

- **Worker Implementation**: `app/workers/job_worker.py`
- **Job Service**: `app/services/implementations/job_service.py`
- **Job Model**: `app/models/job.py`
- **Progress Enum**: `app/models/enum.py`
- **Worker Integration**: `app/__init__.py` (lifespan function)
- **Job Routes**: `app/routers/job_routes.py`

## Notes

- The worker runs as a background task in the FastAPI application
- It starts automatically when the application starts
- It shuts down gracefully when the application stops
- Jobs persist across application restarts
- The database acts as both storage and queue


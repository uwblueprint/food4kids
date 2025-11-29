"""
Job Worker - Processes jobs from database queue.

The database table itself acts as the queue. This worker:
- Polls the database for QUEUED jobs
- Processes them through: QUEUED → RUNNING → COMPLETED/FAILED
- Handles orphaned jobs on startup (jobs stuck in RUNNING state)
- Survives restarts - jobs persist in database
"""
import asyncio
import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import get_session
from app.models.job import Job
from app.models.enum import ProgressEnum
from app.services.implementations.job_service import JobService

logger = logging.getLogger(__name__)


class JobWorker:
    """
    Worker that processes jobs from database queue.
    
    Flow:
    1. Poll database for QUEUED jobs
    2. Mark job as RUNNING
    3. Execute route generation
    4. Mark job as COMPLETED or FAILED
    5. Repeat
    """
    
    def __init__(
        self,
        poll_interval: int = 5,
        job_timeout_minutes: int = 30,
        enable_orphan_recovery: bool = True
    ):
        """
        Initialize the job worker.
        
        Args:
            poll_interval: Seconds to wait between checking for new jobs
            job_timeout_minutes: Max time a job can run before considered stuck
            enable_orphan_recovery: Auto-reset orphaned RUNNING jobs on startup
        """
        self.poll_interval = poll_interval
        self.job_timeout_minutes = job_timeout_minutes
        self.enable_orphan_recovery = enable_orphan_recovery
        
        self.running = False
        self.logger = logging.getLogger(__name__)
    
    async def start(self) -> None:
        """
        Start the worker.
        This is the main entry point that runs the worker loop.
        """
        self.running = True
        self.logger.info("Job worker starting...")
        
        # On startup, handle orphaned jobs (jobs stuck in RUNNING state)
        if self.enable_orphan_recovery:
            await self.recover_orphaned_jobs()
        
        # Start the main worker loop
        await self.worker_loop()
    
    def stop(self) -> None:
        """Stop the worker gracefully"""
        self.logger.info("Stopping job worker...")
        self.running = False
    
    async def worker_loop(self) -> None:
        """
        Main worker loop - continuously polls database for QUEUED jobs.
        """
        self.logger.info("Worker loop started - polling for QUEUED jobs")
        
        while self.running:
            try:
                await self.check_for_stuck_jobs()
                
                await self.process_next_job()
                
            except asyncio.CancelledError:
                self.logger.info("Worker loop cancelled")
                break
            except Exception as e:
                self.logger.exception(f"Error in worker loop: {e}")
                await asyncio.sleep(self.poll_interval)
        
        self.logger.info("Worker loop stopped")
    
    async def process_next_job(self) -> None:
        """
        Find the next QUEUED job and process it.
        Uses SELECT FOR UPDATE SKIP LOCKED to prevent race conditions.
        """
        job_id: UUID | None = None
        
        async for session in get_session():
            try:
                result = await session.execute(
                    select(Job)
                    .where(Job.progress == ProgressEnum.QUEUED)
                    .order_by(Job.created_at)
                    .limit(1)
                    .with_for_update(skip_locked=True)
                )
                job = result.scalar_one_or_none()
                
                if not job:
                    self.logger.debug("No queued jobs found")
                    await asyncio.sleep(self.poll_interval)
                    return
                
                job_id = job.job_id
                self.logger.info(f"Found job {job_id}, processing...")
                
            except Exception as e:
                self.logger.exception(f"Error finding next job: {e}")
                await asyncio.sleep(self.poll_interval)
                return
        
        if job_id:
            await self.process_job(job_id)
    
    async def process_job(self, job_id: UUID) -> None:
        """
        Process a single job.
        Flow: QUEUED → RUNNING → COMPLETED/FAILED
        """
        async for session in get_session():
            job_service = JobService(logger=self.logger, session=session)
            
            try:
                self.logger.info(f"Starting job {job_id}")
                await job_service.update_progress(job_id, ProgressEnum.RUNNING)
                
                job = await job_service.get_job(job_id)
                if not job:
                    self.logger.error(f"Job {job_id} not found, skipping")
                    return
                
                self.logger.info(f"Generating routes for job {job_id}...")
                
                try:
                    await asyncio.wait_for(
                        self.generate_routes(job),
                        timeout=self.job_timeout_minutes * 60
                    )
                except asyncio.TimeoutError:
                    raise Exception(
                        f"Job timed out after {self.job_timeout_minutes} minutes"
                    )
                
                await job_service.update_progress(job_id, ProgressEnum.COMPLETED)
                self.logger.info(f"Job {job_id} completed successfully")
                
            except Exception as e:
                self.logger.exception(f"Job {job_id} failed: {e}")
                
                try:
                    await job_service.update_progress(job_id, ProgressEnum.FAILED)
                except Exception as update_error:
                    self.logger.exception(
                        f"Failed to mark job {job_id} as FAILED: {update_error}"
                    )
    
    async def generate_routes(self, job: Job) -> None:
        """
        Execute the actual route generation algorithm.
        
        TODO: Replace this with your actual implementation.
        """
        self.logger.info(f"Job {job.job_id}: Starting route generation...")
        
        await asyncio.sleep(10)
        
        # TODO: Implement actual route generation

            
    async def recover_orphaned_jobs(self) -> None:
        """
        On startup, find jobs stuck in RUNNING state and reset them to QUEUED.
        This handles jobs that were being processed when the app crashed.
        
        Jobs persist in database, so when app restarts, we can resume processing.
        """
        pass
    
    async def check_for_stuck_jobs(self) -> None:
        """
        Periodically check for jobs that have been RUNNING too long.
        Mark them as FAILED if they exceed the timeout.
        """
        pass


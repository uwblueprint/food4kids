import logging

from fastapi import APIRouter, HTTPException, Query, status

from app.models.enum import ProgressEnum
from app.models.job import JobRead
from app.services.implementations.job_service import JobService

logger = logging.getLogger(__name__)
job_service = JobService(logger)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=list[JobRead])
async def get_jobs(
    progress: ProgressEnum | None = Query(None, description="Filter by job status"),
):
    """Get all jobs"""
    try:
        jobs = await job_service.get_jobs(progress=progress)
        return [JobRead.model_validate(job) for job in jobs]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_session
from app.models.enum import ProgressEnum
from app.models.generation_type import RouteGenerationRequest
from app.models.job import JobCreate, JobRead
from app.services.implementations.job_service import JobService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


def get_job_service(session: AsyncSession = Depends(get_session)) -> JobService:
    return JobService(logger=logger, session=session)


@router.get("/", response_model=list[JobRead])
async def get_jobs(
    progress: ProgressEnum | None = Query(None, description="Filter by job status"),
    service: JobService = Depends(get_job_service),
) -> list[JobRead]:
    """Get all jobs"""
    try:
        jobs = await service.get_jobs(progress=progress)
        return [JobRead.model_validate(job) for job in jobs]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.post(
    "/generate", response_model=list[JobCreate], status_code=status.HTTP_202_ACCEPTED
)
async def create_generation_job(
    req: RouteGenerationRequest,
    service: JobService = Depends(get_job_service),
) -> JobCreate:
    try:
        job = await service.create_generation_job(req)
        await service.enqueue(job.id)
        return {"job_id": job.job_id, "progress": job.progress}
    except Exception as e:
        logger.exception("create_generation_job failed")
        raise HTTPException(status_code=500, detail="Failed to enqueue job") from e

@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: UUID, service: JobService = Depends(get_job_service)
) -> JobRead:
    try:
        job = await service.get_job(job_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    return JobRead.model_validate(job)

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
<<<<<<< HEAD
<<<<<<< HEAD
) -> list[JobRead]:
=======
):
>>>>>>> 653b6fc (add route to get all routes)
=======
) -> list[JobRead]:
>>>>>>> 7c99254 (fix linter errors)
    """Get all jobs"""
    try:
        jobs = await service.get_jobs(progress=progress)
        return [JobRead.model_validate(job) for job in jobs]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
<<<<<<< HEAD
<<<<<<< HEAD
        ) from e
<<<<<<< HEAD
=======
        ) from e
>>>>>>> 653b6fc (add route to get all routes)
=======
        ) from e
>>>>>>> f642f68 (run formatter)
=======


@router.post(
    "/generate", response_model=list[JobCreate], status_code=status.HTTP_202_ACCEPTED
)
async def create_generation_job(
    req: RouteGenerationRequest,
    service: JobService = Depends(get_job_service),
) -> JobCreate:
    job = await service.create_generation_job(req)
    # TODO: enqueue to worker/queue here (stub for skeleton)
    return JobCreate(job_id=str(job.id), status=job.progress)


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: UUID, service: JobService = Depends(get_job_service)
) -> JobRead:
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    return JobRead.model_validate(job)
>>>>>>> 8fdc839 (create inital skeleton for generation service)

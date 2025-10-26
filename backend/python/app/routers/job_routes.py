import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import get_session
from app.models.enum import ProgressEnum
from app.models.job import JobRead
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
) -> list[JobRead]:
=======
):
>>>>>>> 653b6fc (add route to get all routes)
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
=======
        ) from e
>>>>>>> 653b6fc (add route to get all routes)
=======
        ) from e
>>>>>>> f642f68 (run formatter)

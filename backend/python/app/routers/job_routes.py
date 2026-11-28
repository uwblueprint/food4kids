import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_admin
from app.models import get_session
from app.models.enum import ProgressEnum
from app.models.job import JobRead
from app.schemas.generation_responses import JobEnqueueResponse
from app.schemas.route_generation import RouteGenerationGroupInput
from app.services.implementations.job_service import JobService
from app.services.implementations.route_generation_runner import (
    count_group_families_already_routed,
)
from app.services.implementations.route_group_service import double_booking_message

logger = logging.getLogger(__name__)

# Every endpoint here is admin-only: jobs are route-generation runs, driven from
# the admin generation wizard and nothing driver-side.
router = APIRouter(prefix="/jobs", tags=["jobs"])


def get_job_service(session: AsyncSession = Depends(get_session)) -> JobService:
    return JobService(logger=logger, session=session)


@router.get("/", response_model=list[JobRead])
async def get_jobs(
    progress: ProgressEnum | None = Query(None, description="Filter by job status"),
    service: JobService = Depends(get_job_service),
    _auth: bool = Depends(require_admin),
) -> list[JobRead]:
    """Get all jobs"""
    jobs = await service.get_jobs(progress=progress)
    return [JobRead.model_validate(job) for job in jobs]


@router.post("/generate", response_model=JobEnqueueResponse, status_code=202)
async def generate_job(
    req: RouteGenerationGroupInput,
    service: JobService = Depends(get_job_service),
    session: AsyncSession = Depends(get_session),
    _auth: bool = Depends(require_admin),
) -> JobEnqueueResponse:
    """Accept a generation request: persist it as PENDING and wake the worker.

    Admin-only — route generation is an admin workflow, and it burns Maps quota.
    Refused with 400 if any family in the group already has a route that day,
    since a family should be on at most one route per day.
    """
    drive_date = req.settings.route_start_time.date()
    count = await count_group_families_already_routed(
        session, req.location_group, drive_date
    )
    if count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=double_booking_message(count, drive_date),
        )
    job_id = await service.generate_job(req)
    await service.enqueue(job_id)
    return JobEnqueueResponse(job_id=job_id)


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: UUID,
    service: JobService = Depends(get_job_service),
    _auth: bool = Depends(require_admin),
) -> JobRead:
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    return JobRead.model_validate(job)


@router.post("/{job_id}/cancel", response_model=JobRead)
async def cancel_job(
    job_id: UUID,
    service: JobService = Depends(get_job_service),
    _auth: bool = Depends(require_admin),
) -> JobRead:
    """Cancel an in-flight route generation job."""
    job = await service.cancel_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    return JobRead.model_validate(job)

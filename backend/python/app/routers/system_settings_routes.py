from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_admin
from app.dependencies.services import get_scheduler_service, get_system_settings_service
from app.models import get_session
from app.models.system_settings import SystemSettingsRead, SystemSettingsUpdate
from app.services.implementations.scheduler_service import SchedulerService
from app.services.implementations.system_settings_service import SystemSettingsService
from app.services.jobs import refresh_daily_reminder_email_schedule

router = APIRouter(prefix="/system-settings", tags=["system-settings"])


@router.get("/", response_model=SystemSettingsRead | None)
async def get_system_settings(
    session: AsyncSession = Depends(get_session),
    system_settings_service: SystemSettingsService = Depends(
        get_system_settings_service
    ),
    _auth: bool = Depends(require_admin),
) -> SystemSettingsRead | None:
    """Return the singleton system settings row, or null if none has been created."""
    try:
        settings = await system_settings_service.get_settings(session)
        return SystemSettingsRead.model_validate(settings) if settings else None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.patch("/", response_model=SystemSettingsRead)
async def patch_system_settings(
    settings_update: SystemSettingsUpdate,
    session: AsyncSession = Depends(get_session),
    system_settings_service: SystemSettingsService = Depends(
        get_system_settings_service
    ),
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
    _auth: bool = Depends(require_admin),
) -> SystemSettingsRead:
    """Patch the singleton system settings row."""
    try:
        settings = await system_settings_service.update_settings(
            session, settings_update
        )
        await session.commit()
        await session.refresh(settings)
        await refresh_daily_reminder_email_schedule(scheduler_service, session)
        return SystemSettingsRead.model_validate(settings)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        ) from ve
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e

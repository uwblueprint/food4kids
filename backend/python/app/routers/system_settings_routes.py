from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_admin
from app.dependencies.services import get_scheduler_service, get_system_settings_service
from app.models import get_session
from app.models.system_settings import (
    DeliveryTypeRename,
    OrgContactRead,
    SystemSettingsRead,
    SystemSettingsUpdate,
)
from app.services.implementations.scheduler_service import SchedulerService
from app.services.implementations.system_settings_service import (
    DeliveryTypeInUseError,
    DeliveryTypeRenameError,
    SystemSettingsService,
)
from app.services.jobs import refresh_daily_reminder_email_schedule

router = APIRouter(prefix="/system-settings", tags=["system-settings"])


@router.get("/", response_model=SystemSettingsRead)
async def get_system_settings(
    session: AsyncSession = Depends(get_session),
    system_settings_service: SystemSettingsService = Depends(
        get_system_settings_service
    ),
    _auth: bool = Depends(require_admin),
) -> SystemSettingsRead:
    """Return the singleton system settings row.

    Never null — ``ensure_settings`` creates it at startup, and PATCH already
    raises on a missing row, so a soft read here would mean a blank form that
    every save rejects.
    """
    settings = await system_settings_service.require_settings(session)
    return SystemSettingsRead.model_validate(settings)


@router.get("/contact", response_model=OrgContactRead)
async def get_org_contact(
    session: AsyncSession = Depends(get_session),
    system_settings_service: SystemSettingsService = Depends(
        get_system_settings_service
    ),
) -> OrgContactRead:
    """Return the org's point of contact — name and phone — to any caller.

    The only unauthenticated route here, because neither consumer can present
    an admin token: the driver route screen's "Call Food4Kids" button, and the
    catch-all error page, which renders for logged-out visitors. These are the
    org's published contact details, not member data; everything else on the
    settings row stays behind ``require_admin``.
    """
    settings = await system_settings_service.require_settings(session)
    return OrgContactRead.model_validate(settings)


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
    except DeliveryTypeInUseError as e:
        # Subclass of ValueError — must precede the ValueError handler below.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        ) from ve


@router.post("/delivery-types/rename", response_model=SystemSettingsRead)
async def rename_delivery_type(
    body: DeliveryTypeRename,
    session: AsyncSession = Depends(get_session),
    system_settings_service: SystemSettingsService = Depends(
        get_system_settings_service
    ),
    _auth: bool = Depends(require_admin),
) -> SystemSettingsRead:
    """Rename a configured delivery type, cascading onto every location using it."""
    try:
        settings = await system_settings_service.rename_delivery_type(
            session, body.old_name, body.new_name
        )
        await session.commit()
        await session.refresh(settings)
        return SystemSettingsRead.model_validate(settings)
    except DeliveryTypeRenameError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(e),
        ) from e

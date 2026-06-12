from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_admin
from app.dependencies.services import get_system_settings_service
from app.models import get_session
from app.models.system_settings import SystemSettingsRead
from app.services.implementations.system_settings_service import SystemSettingsService

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

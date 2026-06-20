from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies.auth import (
    get_current_database_user_id,
    require_admin,
    require_driver_or_admin,
)
from app.dependencies.services import (
    get_announcement_service,
    get_email_dispatcher_depends,
)
from app.models import get_session
from app.models.announcement import (
    AnnouncementCreate,
    AnnouncementRead,
    AnnouncementUpdate,
)
from app.services.implementations.announcement_service import AnnouncementService
from app.services.implementations.email_dispatcher import EmailDispatcher

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("/", response_model=list[AnnouncementRead])
async def get_announcements(
    session: AsyncSession = Depends(get_session),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
    _auth: bool = Depends(require_driver_or_admin),
) -> list[AnnouncementRead]:
    """Retrieve all announcements"""
    try:
        announcements = await announcement_service.get_announcements(session)
        return [AnnouncementRead.from_announcement(a) for a in announcements]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/{announcement_id}", response_model=AnnouncementRead)
async def get_announcement(
    announcement_id: UUID,
    session: AsyncSession = Depends(get_session),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
    _auth: bool = Depends(require_driver_or_admin),
) -> AnnouncementRead:
    """Get a single announcement by ID"""
    announcement = await announcement_service.get_announcement(session, announcement_id)
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Announcement with id {announcement_id} not found",
        )
    return AnnouncementRead.from_announcement(announcement)


@router.post("/", response_model=AnnouncementRead, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    announcement: AnnouncementCreate,
    session: AsyncSession = Depends(get_session),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
    _auth: bool = Depends(require_driver_or_admin),
    current_user_id: UUID = Depends(get_current_database_user_id),
) -> AnnouncementRead:
    """Create a new announcement"""
    try:
        created_announcement = await announcement_service.create_announcement(
            session, current_user_id, announcement
        )
        return AnnouncementRead.from_announcement(created_announcement)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.put("/{announcement_id}", response_model=AnnouncementRead)
async def update_announcement(
    announcement_id: UUID,
    announcement: AnnouncementUpdate,
    session: AsyncSession = Depends(get_session),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
    _auth: bool = Depends(require_driver_or_admin),
    current_user_id: UUID = Depends(get_current_database_user_id),
) -> AnnouncementRead:
    """Update an existing announcement"""
    try:
        updated_announcement = await announcement_service.update_announcement(
            session, announcement_id, current_user_id, announcement
        )
    except PermissionError as pe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe),
        ) from pe

    if not updated_announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Announcement with id {announcement_id} not found",
        )
    return AnnouncementRead.from_announcement(updated_announcement)


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    announcement_id: UUID,
    session: AsyncSession = Depends(get_session),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
    _auth: bool = Depends(require_driver_or_admin),
    current_user_id: UUID = Depends(get_current_database_user_id),
) -> None:
    """Delete an announcement"""
    try:
        success = await announcement_service.delete_announcement(
            session, announcement_id, current_user_id
        )
    except PermissionError as pe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe),
        ) from pe

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Announcement with id {announcement_id} not found",
        )


@router.post("/{announcement_id}/email")
async def send_announcement_email(
    announcement_id: UUID,
    session: AsyncSession = Depends(get_session),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
    dispatcher: EmailDispatcher = Depends(get_email_dispatcher_depends),
    _auth: bool = Depends(require_admin),
) -> dict[str, int]:
    """Send announcement notification emails to all active drivers (admin only)."""
    try:
        return await announcement_service.send_announcement_emails_to_drivers(
            session,
            announcement_id,
            dispatcher,
            settings.frontend_base_url,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

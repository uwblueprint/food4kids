from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.services import get_announcement_service
from app.models import get_session
from app.models.announcement import (
    AnnouncementCreate,
    AnnouncementRead,
    AnnouncementUpdate,
)
from app.services.implementations.announcement_service import AnnouncementService

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("/", response_model=list[AnnouncementRead])
async def get_announcements(
    session: AsyncSession = Depends(get_session),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
) -> list[AnnouncementRead]:
    """Retrieve all announcements"""
    try:
        announcements = await announcement_service.get_announcements(session)
        return [AnnouncementRead.model_validate(a) for a in announcements]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/{announcement_id}", response_model=AnnouncementRead)
async def get_announcement(
    announcement_id: UUID,
    session: AsyncSession = Depends(get_session),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
) -> AnnouncementRead:
    """Get a single announcement by ID"""
    announcement = await announcement_service.get_announcement(session, announcement_id)
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Announcement with id {announcement_id} not found",
        )
    return AnnouncementRead.model_validate(announcement)


@router.post("/", response_model=AnnouncementRead, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    announcement: AnnouncementCreate,
    session: AsyncSession = Depends(get_session),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
) -> AnnouncementRead:
    """Create a new announcement"""
    try:
        created_announcement = await announcement_service.create_announcement(
            session, announcement
        )
        return AnnouncementRead.model_validate(created_announcement)
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
) -> AnnouncementRead:
    """Update an existing announcement"""
    updated_announcement = await announcement_service.update_announcement(
        session, announcement_id, announcement
    )
    if not updated_announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Announcement with id {announcement_id} not found",
        )
    return AnnouncementRead.model_validate(updated_announcement)


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    announcement_id: UUID,
    session: AsyncSession = Depends(get_session),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
) -> None:
    """Delete an announcement"""
    success = await announcement_service.delete_announcement(session, announcement_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Announcement with id {announcement_id} not found",
        )

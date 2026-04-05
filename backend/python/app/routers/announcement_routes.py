from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.services import get_announcement_service
from app.models import get_session
from app.models.announcement import (
    AnnouncementCreate,
    AnnouncementRead,
    AnnouncementUpdate,
)
from app.models.announcement_last_read import (
    AnnouncementLastReadResponse,
    MarkReadRequest,
)
from app.services.implementations.announcement_service import AnnouncementService

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("/", response_model=list[AnnouncementRead])
async def get_announcements(
    user_id: UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
) -> list[AnnouncementRead]:
    """Retrieve all announcements. If user_id is provided, includes is_read status."""
    try:
        announcements = await announcement_service.get_announcements(session)

        last_read_at = None
        if user_id is not None:
            last_read_at = await announcement_service.get_last_read_at(
                session, user_id
            )

        results = []
        for a in announcements:
            item = AnnouncementRead.model_validate(a)
            if user_id is not None:
                if last_read_at is None:
                    item.is_read = False
                else:
                    item.is_read = (
                        a.created_at is not None and a.created_at <= last_read_at
                    )
            results.append(item)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.post("/mark-read", response_model=AnnouncementLastReadResponse)
async def mark_announcements_as_read(
    body: MarkReadRequest,
    session: AsyncSession = Depends(get_session),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
) -> AnnouncementLastReadResponse:
    """Mark all announcements as read for the given user"""
    try:
        entry = await announcement_service.mark_announcements_as_read(
            session, body.user_id
        )
        return AnnouncementLastReadResponse.model_validate(entry)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e
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

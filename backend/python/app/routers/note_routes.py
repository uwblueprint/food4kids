from enum import Enum
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_database_user_id, require_admin
from app.dependencies.services import get_gcp_storage_client, get_note_chain_service
from app.models import get_session
from app.models.note import NoteFeedItem
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.services.implementations.note_chain_service import NoteChainService
from app.utilities.gcp_client import GCPStorageClient, GCSStorageError
from app.utilities.note_attachments import refresh_attachment_urls


class NoteFeedSort(str, Enum):
    UNREAD = "unread"
    RECENT = "recent"
    OLDEST = "oldest"
    DRIVER = "driver"
    LOCATION = "location"


router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=PaginatedResponse[NoteFeedItem])
async def get_notes_feed(
    sort: NoteFeedSort = Query(
        default=NoteFeedSort.RECENT,
        description="Sort by unread first, recent, oldest, driver, or location",
    ),
    search: str | None = Query(default=None, max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    note_chain_service: NoteChainService = Depends(get_note_chain_service),
    gcp_client: GCPStorageClient = Depends(get_gcp_storage_client),
    _auth: bool = Depends(require_admin),
    current_user_id: UUID = Depends(get_current_database_user_id),
) -> PaginatedResponse[NoteFeedItem]:
    """Get location notes across all location note chains."""
    pagination = PaginationParams(page=page, page_size=page_size)
    try:
        result = await note_chain_service.get_location_notes_feed(
            session, pagination, sort.value, user_id=current_user_id, search=search
        )
        items = [
            item.model_copy(
                update={
                    "attachments": refresh_attachment_urls(
                        item.attachments, gcp_client
                    ),
                }
            )
            for item in result.items
        ]
        return PaginatedResponse.create(
            items=items,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )
    except GCSStorageError as e:
        status_code = 403 if "permission denied" in str(e).lower() else 503
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post("/{note_id}/read", status_code=204)
async def mark_note_read(
    note_id: UUID,
    session: AsyncSession = Depends(get_session),
    note_chain_service: NoteChainService = Depends(get_note_chain_service),
    _auth: bool = Depends(require_admin),
    current_user_id: UUID = Depends(get_current_database_user_id),
) -> None:
    """Mark a location note as viewed for the current admin only."""
    if not await note_chain_service.mark_location_note_read(
        session, note_id, current_user_id
    ):
        raise HTTPException(status_code=404, detail="Location note not found")

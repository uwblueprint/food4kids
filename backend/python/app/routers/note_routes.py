import logging
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_admin
from app.dependencies.services import get_note_chain_service
from app.models import get_session
from app.models.note import NoteFeedItem
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.services.implementations.note_chain_service import NoteChainService

logger = logging.getLogger(__name__)


class NoteFeedSort(str, Enum):
    RECENT = "recent"
    OLDEST = "oldest"
    DRIVER = "driver"
    LOCATION = "location"


router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=PaginatedResponse[NoteFeedItem])
async def get_notes_feed(
    sort: NoteFeedSort = Query(
        default=NoteFeedSort.RECENT,
        description="Sort by recent, oldest, driver, or location",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    limit: int | None = Query(
        default=None,
        ge=1,
        le=200,
        description="Optional alias for page_size; useful for recent widget requests",
    ),
    session: AsyncSession = Depends(get_session),
    note_chain_service: NoteChainService = Depends(get_note_chain_service),
    _auth: bool = Depends(require_admin),
) -> PaginatedResponse[NoteFeedItem]:
    """Get location notes across all location note chains."""
    try:
        pagination = PaginationParams(page=page, page_size=limit or page_size)
        return await note_chain_service.get_location_notes_feed(
            session, pagination, sort.value
        )
    except Exception as e:
        logger.exception("Failed to get notes feed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notes feed",
        ) from e

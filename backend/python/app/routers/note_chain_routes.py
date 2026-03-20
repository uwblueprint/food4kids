import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_database_user_id
from app.dependencies.services import get_note_chain_service
from app.models import get_session
from app.models.note import NoteCreate, NoteListResponse, NoteRead, NoteUpdate
from app.models.note_chain import NoteChainRead, NoteChainUpdate
from app.services.implementations.note_chain_service import NoteChainService

logger = logging.getLogger(__name__)
note_chain_service: NoteChainService = get_note_chain_service()

router = APIRouter(prefix="/note-chains", tags=["note-chains"])


# --- Note Chain endpoints ---


@router.get("/{note_chain_id}", response_model=NoteChainRead)
async def get_note_chain(
    note_chain_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user_id: UUID = Depends(get_current_database_user_id),
) -> NoteChainRead:
    """Get a note chain by ID (checks read permission)"""
    try:
        note_chain = await note_chain_service.get_note_chain_with_permission(
            session, note_chain_id, current_user_id
        )
        return NoteChainRead.model_validate(note_chain)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        ) from ve
    except PermissionError as pe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe),
        ) from pe
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.patch("/{note_chain_id}", response_model=NoteChainRead)
async def update_note_chain(
    note_chain_id: UUID,
    data: NoteChainUpdate,
    session: AsyncSession = Depends(get_session),
    current_user_id: UUID = Depends(get_current_database_user_id),
) -> NoteChainRead:
    """Update a note chain's permissions (admin only)"""
    try:
        note_chain = await note_chain_service.update_note_chain(
            session, note_chain_id, data, current_user_id
        )
        return NoteChainRead.model_validate(note_chain)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        ) from ve
    except PermissionError as pe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe),
        ) from pe
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.delete("/{note_chain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note_chain(
    note_chain_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user_id: UUID = Depends(get_current_database_user_id),
) -> None:
    """Delete a note chain and all its notes (admin only)"""
    try:
        await note_chain_service.delete_note_chain(
            session, note_chain_id, current_user_id
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        ) from ve
    except PermissionError as pe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe),
        ) from pe
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


# --- Notes endpoints ---


@router.get("/{note_chain_id}/notes", response_model=NoteListResponse)
async def get_notes(
    note_chain_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user_id: UUID = Depends(get_current_database_user_id),
) -> NoteListResponse:
    """Get notes for a chain with pagination. Returns unread count and auto-marks as read."""
    try:
        # Get unread count before marking as read
        unread_count = await note_chain_service.get_unread_count(
            session, note_chain_id, current_user_id
        )

        notes = await note_chain_service.get_notes_by_chain_id(
            session, note_chain_id, current_user_id, limit, offset
        )

        # Auto-mark as read
        await note_chain_service.mark_chain_as_read(
            session, note_chain_id, current_user_id
        )

        return NoteListResponse(
            notes=[NoteRead.model_validate(note) for note in notes],
            unread_count=unread_count,
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        ) from ve
    except PermissionError as pe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe),
        ) from pe
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post(
    "/{note_chain_id}/notes",
    response_model=NoteRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_note(
    note_chain_id: UUID,
    data: NoteCreate,
    session: AsyncSession = Depends(get_session),
    current_user_id: UUID = Depends(get_current_database_user_id),
) -> NoteRead:
    """Add a note to a chain"""
    try:
        note = await note_chain_service.create_note(
            session, note_chain_id, current_user_id, data
        )
        return NoteRead.model_validate(note)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        ) from ve
    except PermissionError as pe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe),
        ) from pe
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.patch("/{note_chain_id}/notes/{note_id}", response_model=NoteRead)
async def update_note(
    note_chain_id: UUID,
    note_id: UUID,
    data: NoteUpdate,
    session: AsyncSession = Depends(get_session),
    current_user_id: UUID = Depends(get_current_database_user_id),
) -> NoteRead:
    """Edit a note's message (author or admin only)"""
    try:
        note = await note_chain_service.update_note(
            session, note_chain_id, note_id, current_user_id, data
        )
        return NoteRead.model_validate(note)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        ) from ve
    except PermissionError as pe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe),
        ) from pe
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.delete(
    "/{note_chain_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_note(
    note_chain_id: UUID,
    note_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user_id: UUID = Depends(get_current_database_user_id),
) -> None:
    """Delete a note (author or admin only)"""
    try:
        await note_chain_service.delete_note(
            session, note_chain_id, note_id, current_user_id
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        ) from ve
    except PermissionError as pe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe),
        ) from pe
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import get_session
from ..dependencies.auth import require_user_or_admin
from ..models.entity import EntityCreate, EntityUpdate, EntityRead
from ..services.implementations.entity_service import EntityService

# Initialize service
logger = logging.getLogger(__name__)
entity_service = EntityService(logger)

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("/", response_model=List[EntityRead])
async def get_entities(
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_user_or_admin),
) -> List[EntityRead]:
    """
    Get all entities - Modern FastAPI approach
    """
    try:
        entities = await entity_service.get_entities(session)
        # FastAPI automatically converts Entity -> EntityRead
        return entities
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{entity_id}", response_model=EntityRead)
async def get_entity(
    entity_id: int,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_user_or_admin),
) -> EntityRead:
    """
    Get a single entity by ID
    """
    entity = await entity_service.get_entity(session, entity_id)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity with id {entity_id} not found"
        )
    return entity


@router.post("/", response_model=EntityRead, status_code=status.HTTP_201_CREATED)
async def create_entity(
    entity: EntityCreate,  # Auto-validated by FastAPI
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_user_or_admin),
) -> EntityRead:
    """
    Create a new entity
    """
    try:
        created_entity = await entity_service.create_entity(session, entity)
        return created_entity
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{entity_id}", response_model=EntityRead)
async def update_entity(
    entity_id: int,
    entity: EntityUpdate,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_user_or_admin),
) -> EntityRead:
    """
    Update an existing entity
    """
    updated_entity = await entity_service.update_entity(session, entity_id, entity)
    if not updated_entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity with id {entity_id} not found"
        )
    return updated_entity


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    entity_id: int,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_user_or_admin),
):
    """
    Delete an entity
    """
    success = await entity_service.delete_entity(session, entity_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity with id {entity_id} not found"
        )

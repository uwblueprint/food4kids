import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import get_session
from ..dependencies.auth import require_user_or_admin
from ..models.simple_entity import SimpleEntityCreate, SimpleEntityUpdate, SimpleEntityRead
from ..services.implementations.simple_entity_service import SimpleEntityService

# Initialize service
logger = logging.getLogger(__name__)
simple_entity_service = SimpleEntityService(logger)

router = APIRouter(prefix="/simple-entities", tags=["simple-entities"])


@router.get("/", response_model=List[SimpleEntityRead])
async def get_simple_entities(
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_user_or_admin),
) -> List[SimpleEntityRead]:
    """
    Get all simple entities - Modern FastAPI approach
    """
    try:
        simple_entities = await simple_entity_service.get_simple_entities(session)
        # FastAPI automatically converts SimpleEntity -> SimpleEntityRead
        return simple_entities
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{simple_entity_id}", response_model=SimpleEntityRead)
async def get_simple_entity(
    simple_entity_id: int,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_user_or_admin),
) -> SimpleEntityRead:
    """
    Get a single simple entity by ID
    """
    simple_entity = await simple_entity_service.get_simple_entity(session, simple_entity_id)
    if not simple_entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SimpleEntity with id {simple_entity_id} not found"
        )
    return simple_entity


@router.post("/", response_model=SimpleEntityRead, status_code=status.HTTP_201_CREATED)
async def create_simple_entity(
    simple_entity: SimpleEntityCreate,  # Auto-validated by FastAPI
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_user_or_admin),
) -> SimpleEntityRead:
    """
    Create a new simple entity
    """
    try:
        created_simple_entity = await simple_entity_service.create_simple_entity(session, simple_entity)
        return created_simple_entity
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{simple_entity_id}", response_model=SimpleEntityRead)
async def update_simple_entity(
    simple_entity_id: int,
    simple_entity: SimpleEntityUpdate,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_user_or_admin),
) -> SimpleEntityRead:
    """
    Update an existing simple entity
    """
    updated_simple_entity = await simple_entity_service.update_simple_entity(session, simple_entity_id, simple_entity)
    if not updated_simple_entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SimpleEntity with id {simple_entity_id} not found"
        )
    return updated_simple_entity


@router.delete("/{simple_entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_simple_entity(
    simple_entity_id: int,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_user_or_admin),
):
    """
    Delete a simple entity
    """
    success = await simple_entity_service.delete_simple_entity(session, simple_entity_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SimpleEntity with id {simple_entity_id} not found"
        )

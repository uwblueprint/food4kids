from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_driver
from app.dependencies.services import get_entity_service
from app.models import get_session
from app.models.entity import EntityCreate, EntityRead, EntityUpdate
from app.services.implementations.entity_service import EntityService

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("/", response_model=list[EntityRead])
async def get_entities(
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
    entity_service: EntityService = Depends(get_entity_service),
) -> list[EntityRead]:
    """
    Get all entities - Modern FastAPI approach
    """
    try:
        entities = await entity_service.get_entities(session)
        return [EntityRead.model_validate(entity) for entity in entities]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/{entity_id}", response_model=EntityRead)
async def get_entity(
    entity_id: int,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
    entity_service: EntityService = Depends(get_entity_service),
) -> EntityRead:
    """
    Get a single entity by ID
    """
    entity = await entity_service.get_entity(session, entity_id)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity with id {entity_id} not found",
        )
    return EntityRead.model_validate(entity)


@router.post("/", response_model=EntityRead, status_code=status.HTTP_201_CREATED)
async def create_entity(
    entity: EntityCreate,  # Auto-validated by FastAPI
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
    entity_service: EntityService = Depends(get_entity_service),
) -> EntityRead:
    """
    Create a new entity
    """
    try:
        created_entity = await entity_service.create_entity(session, entity)
        return EntityRead.model_validate(created_entity)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.put("/{entity_id}", response_model=EntityRead)
async def update_entity(
    entity_id: int,
    entity: EntityUpdate,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
    entity_service: EntityService = Depends(get_entity_service),
) -> EntityRead:
    """
    Update an existing entity
    """
    updated_entity = await entity_service.update_entity(session, entity_id, entity)
    if not updated_entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity with id {entity_id} not found",
        )
    return EntityRead.model_validate(updated_entity)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    entity_id: int,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
    entity_service: EntityService = Depends(get_entity_service),
) -> None:
    """
    Delete an entity
    """
    success = await entity_service.delete_entity(session, entity_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity with id {entity_id} not found",
        )

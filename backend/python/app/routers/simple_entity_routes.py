from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_driver
from app.dependencies.services import get_simple_entity_service
from app.models import get_session
from app.models.simple_entity import (
    SimpleEntityCreate,
    SimpleEntityRead,
    SimpleEntityUpdate,
)
from app.services.implementations.simple_entity_service import SimpleEntityService

router = APIRouter(prefix="/simple-entities", tags=["simple-entities"])


@router.get("/", response_model=list[SimpleEntityRead])
async def get_simple_entities(
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
    simple_entity_service: SimpleEntityService = Depends(get_simple_entity_service),
) -> list[SimpleEntityRead]:
    """
    Retrieve all simple entities
    """
    try:
        simple_entities = await simple_entity_service.get_simple_entities(session)
        # FastAPI automatically converts SimpleEntity -> SimpleEntityRead
        return [SimpleEntityRead.model_validate(entity) for entity in simple_entities]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/{simple_entity_id}", response_model=SimpleEntityRead)
async def get_simple_entity(
    simple_entity_id: int,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
    simple_entity_service: SimpleEntityService = Depends(get_simple_entity_service),
) -> SimpleEntityRead:
    """
    Get a single simple entity by ID
    """
    simple_entity = await simple_entity_service.get_simple_entity(
        session, simple_entity_id
    )
    if not simple_entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SimpleEntity with id {simple_entity_id} not found",
        )
    return SimpleEntityRead.model_validate(simple_entity)


@router.post("/", response_model=SimpleEntityRead, status_code=status.HTTP_201_CREATED)
async def create_simple_entity(
    simple_entity: SimpleEntityCreate,  # Auto-validated by FastAPI
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
    simple_entity_service: SimpleEntityService = Depends(get_simple_entity_service),
) -> SimpleEntityRead:
    """
    Create a new simple entity
    """
    try:
        created_simple_entity = await simple_entity_service.create_simple_entity(
            session, simple_entity
        )
        return SimpleEntityRead.model_validate(created_simple_entity)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.put("/{simple_entity_id}", response_model=SimpleEntityRead)
async def update_simple_entity(
    simple_entity_id: int,
    simple_entity: SimpleEntityUpdate,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
    simple_entity_service: SimpleEntityService = Depends(get_simple_entity_service),
) -> SimpleEntityRead:
    """
    Update an existing simple entity
    """
    updated_simple_entity = await simple_entity_service.update_simple_entity(
        session, simple_entity_id, simple_entity
    )
    if not updated_simple_entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SimpleEntity with id {simple_entity_id} not found",
        )
    return SimpleEntityRead.model_validate(updated_simple_entity)


@router.delete("/{simple_entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_simple_entity(
    simple_entity_id: int,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
    simple_entity_service: SimpleEntityService = Depends(get_simple_entity_service),
) -> None:
    """
    Delete a simple entity
    """
    success = await simple_entity_service.delete_simple_entity(
        session, simple_entity_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SimpleEntity with id {simple_entity_id} not found",
        )

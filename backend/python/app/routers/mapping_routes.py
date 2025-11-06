import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# from app.dependencies.auth import require_driver
from app.models import get_session
from app.models.location_mappings import (
    LocationMappingCreate,
    LocationMappingRead,
)
from app.services.implementations.mappings_service import MappingsService

# Initialize service
logger = logging.getLogger(__name__)
mappings_service = MappingsService(logger)
router = APIRouter(prefix="/mappings", tags=["mappings"])


@router.get("/", response_model=list[LocationMappingRead])
async def get_location_mappings(
    session: AsyncSession = Depends(get_session),
    # _: bool = Depends(require_driver),
) -> list[LocationMappingRead]:
    """
    Get all location mappings
    """
    try:
        mappings = await mappings_service.get_mappings(session)
        return [LocationMappingRead.model_validate(mapping) for mapping in mappings]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("/", response_model=LocationMappingCreate, status_code=status.HTTP_201_CREATED)
async def create_location_mapping(
    mapping: LocationMappingCreate,
    session: AsyncSession = Depends(get_session),
    # _: bool = Depends(require_driver),
) -> LocationMappingRead:
    """
    Create a new location mapping
    """
    try:
        created_mapping = await mappings_service.create_mapping(session, mapping)
        return LocationMappingRead.model_validate(created_mapping)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e

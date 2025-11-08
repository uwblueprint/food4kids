import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

# from app.dependencies.auth import require_driver
from app.models import get_session
from app.models.location_mappings import (
    LocationMappingCreate,
    LocationMappingPreview,
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


@router.get("/{mapping_id}", response_model=LocationMappingRead)
async def get_location_mapping(
    mapping_id: UUID,
    session: AsyncSession = Depends(get_session),
    # _: bool = Depends(require_driver),
) -> LocationMappingRead:
    """
    Get a single location mapping by ID
    """
    try:
        mapping = await mappings_service.get_mapping_by_id(session, mapping_id)
        return LocationMappingRead.model_validate(mapping)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        ) from ve
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("/submit", response_model=LocationMappingCreate, status_code=status.HTTP_201_CREATED)
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


@router.post("/preview", response_model=LocationMappingPreview, status_code=status.HTTP_200_OK)
async def preview_location_mapping(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    # _: bool = Depends(require_driver),
) -> LocationMappingPreview:
    """
    Preview a location mapping from an uploaded file
    """
    try:
        preview = await mappings_service.preview_mapping(file)
        return LocationMappingPreview.model_validate(preview)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location_mappings(
    session: AsyncSession = Depends(get_session),
    # _: bool = Depends(require_driver),
) -> None:
    """
    Delete a location mapping
    """
    try:
        await mappings_service.delete_mappings(session)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e

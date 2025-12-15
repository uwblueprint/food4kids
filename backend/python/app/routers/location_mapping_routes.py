import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# from app.dependencies.auth import require_driver
from app.models import get_session
from app.models.location_mappings import (
    LocationMappingCreate,
    LocationMappingRead,
    LocationMappingUpdate,
)
from app.services.implementations.location_mapping_service import LocationMappingService

# Initialize service
logger = logging.getLogger(__name__)
location_mapping_service = LocationMappingService(logger)

router = APIRouter(prefix="/location-mappings", tags=["location-mappings"])


@router.get("/", response_model=list[LocationMappingRead])
async def get_location_mappings(
    session: AsyncSession = Depends(get_session),
    # _: bool = Depends(require_driver),
) -> list[LocationMappingRead]:
    """
    Get all location mappings for users
    """
    try:
        location_mappings = await location_mapping_service.get_location_mappings(
            session
        )
        return [LocationMappingRead.model_validate(lm) for lm in location_mappings]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get("/{location_mapping_id}", response_model=LocationMappingRead)
async def get_location_mapping(
    location_mapping_id: UUID,
    session: AsyncSession = Depends(get_session),
    # _: bool = Depends(require_driver),
) -> LocationMappingRead:
    """
    Get a single location mapping by ID
    """
    try:
        location_mapping = await location_mapping_service.get_location_mapping_by_id(
            session, location_mapping_id
        )
        return LocationMappingRead.model_validate(location_mapping)
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


@router.post(
    "/", response_model=LocationMappingRead, status_code=status.HTTP_201_CREATED
)
async def create_location_mapping(
    location_mapping: LocationMappingCreate,
    session: AsyncSession = Depends(get_session),
    # _: bool = Depends(require_driver),
) -> LocationMappingRead:
    """
    Create a new location mapping for a user
    """
    try:
        created_location_mapping = (
            await location_mapping_service.create_location_mapping(
                session, location_mapping
            )
        )
        return LocationMappingRead.model_validate(created_location_mapping)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.patch(
    "/{location_mapping_id}",
    response_model=LocationMappingRead,
    status_code=status.HTTP_200_OK,
)
async def update_location_mapping(
    location_mapping_id: UUID,
    updated_location_mapping_data: LocationMappingUpdate,
    session: AsyncSession = Depends(get_session),
    # _: bool = Depends(require_driver),
) -> LocationMappingRead:
    """
    Update a location mapping by ID
    """
    try:
        updated_location_mapping = (
            await location_mapping_service.update_location_mapping_by_id(
                session, location_mapping_id, updated_location_mapping_data
            )
        )
        return LocationMappingRead.model_validate(updated_location_mapping)

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


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_location_mappings(
    session: AsyncSession = Depends(get_session),
    # _: bool = Depends(require_driver),
) -> None:
    """
    Delete all location mappings
    """
    try:
        await location_mapping_service.delete_all_location_mappings(session)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.delete("/{location_mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location_mapping(
    location_mapping_id: UUID,
    session: AsyncSession = Depends(get_session),
    # _: bool = Depends(require_driver),
) -> None:
    """
    Delete a location mapping by ID
    """
    try:
        await location_mapping_service.delete_location_mapping_by_id(
            session, location_mapping_id
        )
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

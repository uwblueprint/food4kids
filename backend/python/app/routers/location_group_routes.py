from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_driver
from app.dependencies.services import get_location_group_service
from app.models import get_session
from app.models.location_group import (
    LocationGroupCreate,
    LocationGroupRead,
    LocationGroupUpdate,
)
from app.services.implementations.location_group_service import LocationGroupService

router = APIRouter(prefix="/location-groups", tags=["location-groups"])


@router.get("/", response_model=list[LocationGroupRead])
async def get_location_groups(
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
    location_group_service: LocationGroupService = Depends(get_location_group_service),
) -> list[LocationGroupRead]:
    """
    Get all location groups
    """
    try:
        location_groups = await location_group_service.get_location_groups(session)
        return [LocationGroupRead.model_validate(lg) for lg in location_groups]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/{location_group_id}", response_model=LocationGroupRead)
async def get_location_group(
    location_group_id: UUID,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
    location_group_service: LocationGroupService = Depends(get_location_group_service),
) -> LocationGroupRead:
    """
    Get a single location group by ID
    """
    location_group = await location_group_service.get_location_group(
        session, location_group_id
    )
    if not location_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location group with id {location_group_id} not found",
        )
    return LocationGroupRead.model_validate(location_group)


@router.post("/", response_model=LocationGroupRead, status_code=status.HTTP_201_CREATED)
async def create_location_group(
    location_group: LocationGroupCreate,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
    location_group_service: LocationGroupService = Depends(get_location_group_service),
) -> LocationGroupRead:
    """
    Create a new location group
    """
    try:
        new_location_group = await location_group_service.create_location_group(
            session, location_group
        )
        return LocationGroupRead.model_validate(new_location_group)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.patch("/{location_group_id}", response_model=LocationGroupRead)
async def update_location_group(
    location_group_id: UUID,
    location_group: LocationGroupUpdate,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
    location_group_service: LocationGroupService = Depends(get_location_group_service),
) -> LocationGroupRead:
    """
    Update an existing location group
    """
    updated_location_group = await location_group_service.update_location_group(
        session, location_group_id, location_group
    )
    if not updated_location_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location group with id {location_group_id} not found",
        )
    return LocationGroupRead.model_validate(updated_location_group)


@router.delete("/{location_group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location_group(
    location_group_id: UUID,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_driver),
    location_group_service: LocationGroupService = Depends(get_location_group_service),
) -> None:
    """
    Delete a location group by ID
    """
    success = await location_group_service.delete_location_group(
        session, location_group_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location group with id {location_group_id} not found",
        )

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_driver
from app.dependencies.services import get_location_group_service
from app.models import get_session
from app.models.location_group import LocationGroupRead, LocationGroupUpdate
from app.services.implementations.location_group_service import LocationGroupService

router = APIRouter(prefix="/location-groups", tags=["location-groups"])


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

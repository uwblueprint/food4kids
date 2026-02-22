from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.services import get_location_service

# from app.dependencies.auth import require_driver
from app.models import get_session
from app.models.location import (
    LocationCreate,
    LocationDeduplicationRequest,
    LocationDeduplicationResponse,
    LocationImportResponse,
    LocationImportRow,
    LocationIngestRequest,
    LocationIngestResponse,
    LocationRead,
    LocationUpdate,
)
from app.services.implementations.location_service import LocationService

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/", response_model=list[LocationRead])
async def get_locations(
    session: AsyncSession = Depends(get_session),
    location_service: LocationService = Depends(get_location_service),
    # _: bool = Depends(require_driver),
) -> list[LocationRead]:
    """
    Get all locations
    """
    try:
        locations = await location_service.get_locations(session)
        return [LocationRead.model_validate(location) for location in locations]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get("/{location_id}", response_model=LocationRead)
async def get_location(
    location_id: UUID,
    session: AsyncSession = Depends(get_session),
    location_service: LocationService = Depends(get_location_service),
    # _: bool = Depends(require_driver),
) -> LocationRead:
    """
    Get a single location by ID
    """
    try:
        location = await location_service.get_location_by_id(session, location_id)
        return LocationRead.model_validate(location)
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


@router.post("/", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
async def create_location(
    location: LocationCreate,
    session: AsyncSession = Depends(get_session),
    location_service: LocationService = Depends(get_location_service),
    # _: bool = Depends(require_driver),
) -> LocationRead:
    """
    Create a new location
    """
    try:
        created_location = await location_service.create_location(session, location)
        return LocationRead.model_validate(created_location)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.patch(
    "/{location_id}", response_model=LocationRead, status_code=status.HTTP_200_OK
)
async def update_location(
    location_id: UUID,
    updated_location_data: LocationUpdate,
    session: AsyncSession = Depends(get_session),
    location_service: LocationService = Depends(get_location_service),
    # _: bool = Depends(require_driver),
) -> LocationRead:
    """
    Update a location by ID
    """
    try:
        updated_location = await location_service.update_location_by_id(
            session, location_id, updated_location_data
        )
        return LocationRead.model_validate(updated_location)

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
async def delete_all_locations(
    session: AsyncSession = Depends(get_session),
    location_service: LocationService = Depends(get_location_service),
    # _: bool = Depends(require_driver),
) -> None:
    """
    Delete all locations
    """
    try:
        await location_service.delete_all_locations(session)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: UUID,
    session: AsyncSession = Depends(get_session),
    location_service: LocationService = Depends(get_location_service),
    # _: bool = Depends(require_driver),
) -> None:
    """
    Delete a location by ID
    """
    try:
        await location_service.delete_location_by_id(session, location_id)
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
    "/validate",
    response_model=LocationImportResponse,
    status_code=status.HTTP_200_OK,
)
async def validate_locations(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    location_service: LocationService = Depends(get_location_service),
    # _: bool = Depends(require_driver),
) -> LocationImportResponse:
    """
    Validate location import data (no missing fields or local duplicates)
    """
    try:
        result = await location_service.validate_locations(session, file)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post(
    "/deduplicate",
    response_model=LocationDeduplicationResponse,
    status_code=status.HTTP_200_OK,
)
async def deduplicate_locations(
    request: LocationDeduplicationRequest,
    session: AsyncSession = Depends(get_session),
    location_service: LocationService = Depends(get_location_service),
) -> LocationDeduplicationResponse:
    """
    Deduplicate import rows against existing DB locations as net new, similar, or duplicate. Also return stale entries in the db.
    """
    try:
        return await location_service.deduplicate_locations(session, request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post(
    "/ingest",
    response_model=LocationIngestResponse,
    status_code=status.HTTP_200_OK,
)
async def ingest_locations(
    request: LocationIngestRequest,
    session: AsyncSession = Depends(get_session),
    location_service: LocationService = Depends(get_location_service),
) -> LocationIngestResponse:
    """
    Ingest locations: create net new entries, resolve conflicts (accept/deny),
    and archive stale entries.
    """
    try:
        return await location_service.ingest_locations(session, request)
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

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

# from app.dependencies.auth import require_driver
from app.models import get_session
from app.models.location import (
    IngestLocationsPayload,
    IngestLocationsResponse,
    LinkLocationsResponse,
    LocationCreate,
    LocationEntriesResponse,
    LocationLinkPayload,
    LocationRead,
    LocationUpdate,
)
from app.services.implementations.location_group_service import (
    LocationGroupService,
)
from app.services.implementations.location_service import LocationService
from app.services.implementations.mappings_service import MappingsService
from app.utilities.google_maps_client import GoogleMapsClient
from app.utilities.import_utils import CSV_FILE_TYPES, XLSX_FILE_TYPES

# Initialize service
logger = logging.getLogger(__name__)
maps_service = GoogleMapsClient()
location_group_service = LocationGroupService(logger)
mappings_service = MappingsService(logger)
location_service = LocationService(
    logger, maps_service, mappings_service, location_group_service)
router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/", response_model=list[LocationRead])
async def get_locations(
    session: AsyncSession = Depends(get_session),
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


@router.post(
    "/validate",
    response_model=LocationEntriesResponse,
    status_code=status.HTTP_200_OK,
)
async def validate_locations(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    # _: bool = Depends(require_driver),
) -> LocationEntriesResponse:
    """
    Validate location Apricot data (no missing fields or local duplicates)
    """
    if file.content_type not in CSV_FILE_TYPES + XLSX_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only CSV or XLSX files are allowed.",
        )

    try:
        result = await location_service.validate_locations(session, file)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post(
    "/link",
    response_model=LinkLocationsResponse,
    status_code=status.HTTP_200_OK,
)
async def link_locations(
    locations: LocationLinkPayload,
    session: AsyncSession = Depends(get_session),
    # _: bool = Depends(require_driver),
) -> LinkLocationsResponse:
    """
    Link locations from local import and database
    """
    try:
        result = await location_service.link_locations(session, locations)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post(
    "/ingest",
    response_model=IngestLocationsResponse,
    status_code=status.HTTP_200_OK,
)
async def ingest_locations(
    locations: IngestLocationsPayload,
    session: AsyncSession = Depends(get_session),
    # _: bool = Depends(require_driver),
) -> IngestLocationsResponse:
    """
    Ingest locations into the database
    """
    try:
        result = await location_service.ingest_locations(session, locations)
        return result
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

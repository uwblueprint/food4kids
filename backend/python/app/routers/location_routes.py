import json
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_admin
from app.dependencies.services import get_location_service
from app.models import get_session
from app.models.enum import DeliveryTypeEnum, LocationStatusEnum
from app.models.location import (
    LocationCreate,
    LocationImportResponse,
    LocationIngestRequest,
    LocationIngestResponse,
    LocationRead,
    LocationUpdate,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams, get_pagination
from app.services.implementations.location_service import LocationService

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/", response_model=PaginatedResponse[LocationRead])
async def get_locations(
    delivery_type: list[DeliveryTypeEnum] | None = Query(
        None, description="Filter by one or more delivery types"
    ),
    status_filter: list[LocationStatusEnum] | None = Query(
        None, alias="status", description="Filter by one or more location statuses"
    ),
    location_group_id: list[UUID] | None = Query(
        None, description="Filter by one or more location groups"
    ),
    pagination: PaginationParams = Depends(get_pagination),
    session: AsyncSession = Depends(get_session),
    location_service: LocationService = Depends(get_location_service),
    _auth: bool = Depends(require_admin),
) -> PaginatedResponse[LocationRead]:
    """
    Get all locations with pagination
    """
    try:
        # Return the service result as-is: it already builds LocationRead
        # items with has_future_route populated (so the computed `status` is
        # correct). Re-validating each item here would reset has_future_route.
        return await location_service.get_locations(
            session, pagination, delivery_type, status_filter, location_group_id
        )
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
    _auth: bool = Depends(require_admin),
) -> LocationRead:
    """
    Get a single location by ID
    """
    try:
        return await location_service.get_location_read_by_id(session, location_id)
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
    _auth: bool = Depends(require_admin),
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
    _auth: bool = Depends(require_admin),
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
    _auth: bool = Depends(require_admin),
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
    _auth: bool = Depends(require_admin),
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
    "/review",
    response_model=LocationImportResponse,
    status_code=status.HTTP_200_OK,
)
async def review_locations(
    file: UploadFile = File(...),
    column_map: str = Form(...),
    session: AsyncSession = Depends(get_session),
    location_service: LocationService = Depends(get_location_service),
    _auth: bool = Depends(require_admin),
) -> LocationImportResponse:
    """
    Review a pending location import: validate rows and (eventually) describe how
    the import would affect existing locations (net_new / stale / changed).
    Requires a column_map JSON string mapping system field names to file headers.

    Side effect: the submitted column_map is persisted to system_settings so it
    becomes the default mapping on the next import.
    """
    try:
        try:
            parsed_map: dict[str, str] = json.loads(column_map)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid column_map JSON: {e}") from e
        result = await location_service.review_locations(session, file, parsed_map)
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        ) from ve
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
    _auth: bool = Depends(require_admin),
) -> LocationIngestResponse:
    """
    Persist net-new locations and archive stale ones.
    """
    try:
        return await location_service.ingest_locations(session, request)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        ) from ve
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e

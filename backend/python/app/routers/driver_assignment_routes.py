import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import require_user_or_admin
from app.models import get_session
from app.models.driver_assignment import DriverAssignmentCreate, DriverAssignmentRead
from app.services.implementations.driver_assignment_service import DriverAssignmentService

# Initialize service
logger = logging.getLogger(__name__)
driver_assignment_service = DriverAssignmentService(logger)

router = APIRouter(prefix="/driver-assignments", tags=["driver-assignments"])

@router.post("/", response_model=DriverAssignmentRead, status_code=status.HTTP_201_CREATED)
async def create_driver_assignment(
    driver_assignment: DriverAssignmentCreate,  # Auto-validated by FastAPI
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(require_user_or_admin),
) -> DriverAssignmentRead:
    """
    Create a new driver assignment
    """
    try:
        created_driver_assignment = await driver_assignment_service.create_driver_assignment(session, driver_assignment)
        return DriverAssignmentRead.model_validate(created_driver_assignment)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


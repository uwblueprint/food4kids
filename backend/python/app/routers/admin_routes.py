import logging

from fastapi import APIRouter, Depends

from app.dependencies.auth import require_authorization_by_role
from app.services.implementations.driver_service import DriverService

# Initialize service
logger = logging.getLogger(__name__)
driver_service = DriverService(logger)

router = APIRouter(prefix="/admins", tags=["admins"])


@router.get("/test", response_model=str)
async def test(
    _: bool = Depends(require_authorization_by_role({"admin"})),
) -> str:
    """
    Admin only route example
    """
    return "Admin only hehehehehehe - hy lac"

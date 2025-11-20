import logging
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List

from app.models import get_session
from app.models.polyline import Polyline, PolylineCreate, PolylineRead, PolylineUpdate
from app.models.route import Route

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/polylines", tags=["polylines"])


@router.get("/", response_model=List[PolylineRead])
async def get_polylines(
    session: AsyncSession = Depends(get_session),
) -> List[Polyline]:
    """Get all polylines"""
    result = await session.execute(select(Polyline))
    return result.scalars().all()


@router.get("/route/{route_id}", response_model=List[PolylineRead])
async def get_polylines_by_route(
    route_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> List[Polyline]:
    """Get all polylines for a specific route"""
    result = await session.execute(
        select(Polyline).where(Polyline.route_id == route_id)
    )
    return result.scalars().all()


@router.get("/expired", response_model=List[PolylineRead])
async def get_expired_polylines(
    session: AsyncSession = Depends(get_session),
) -> List[Polyline]:
    """Get all expired polylines"""
    now = datetime.utcnow()
    result = await session.execute(
        select(Polyline).where(Polyline.expires_at < now)
    )
    return result.scalars().all()


@router.post("/", response_model=PolylineRead, status_code=status.HTTP_201_CREATED)
async def create_polyline(
    polyline: PolylineCreate,
    session: AsyncSession = Depends(get_session),
) -> Polyline:
    """Create a new polyline"""
    db_polyline = Polyline(**polyline.dict())
    session.add(db_polyline)
    await session.commit()
    await session.refresh(db_polyline)
    return db_polyline


@router.get("/{polyline_id}", response_model=PolylineRead)
async def get_polyline(
    polyline_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> Polyline:
    """Get a polyline by ID"""
    result = await session.execute(
        select(Polyline).where(Polyline.polyline_id == polyline_id)
    )
    db_polyline = result.scalar_one_or_none()
    if db_polyline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Polyline with id {polyline_id} not found",
        )
    return db_polyline


@router.put("/{polyline_id}", response_model=PolylineRead)
async def update_polyline(
    polyline_id: UUID,
    polyline_update: PolylineUpdate,
    session: AsyncSession = Depends(get_session),
) -> Polyline:
    """Update a polyline"""
    result = await session.execute(
        select(Polyline).where(Polyline.polyline_id == polyline_id)
    )
    db_polyline = result.scalar_one_or_none()
    if db_polyline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Polyline with id {polyline_id} not found",
        )

    update_data = polyline_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_polyline, field, value)

    await session.commit()
    await session.refresh(db_polyline)
    return db_polyline


@router.delete("/{polyline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_polyline(
    polyline_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a polyline"""
    result = await session.execute(
        select(Polyline).where(Polyline.polyline_id == polyline_id)
    )
    db_polyline = result.scalar_one_or_none()
    if db_polyline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Polyline with id {polyline_id} not found",
        )

    await session.delete(db_polyline)
    await session.commit()


@router.get("/route/{route_id}", response_model=List[PolylineRead])
async def get_polylines_by_route(
    route_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> List[Polyline]:
    """Get all polylines for a specific route"""
    result = await session.execute(
        select(Polyline).where(Polyline.route_id == route_id)
    )
    return result.scalars().all()


@router.post("/cleanup-expired", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expired_polylines(
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete all expired polylines (where expires_at < now)"""
    now = datetime.utcnow()
    await session.execute(
        delete(Polyline).where(Polyline.expires_at < now)
    )
    await session.commit()

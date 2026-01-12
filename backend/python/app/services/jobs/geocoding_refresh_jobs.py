"""Geocoding refresh scheduled jobs"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

from sqlalchemy import and_, or_
from sqlmodel import select

from app.dependencies.services import get_logger
from app.models import async_session_maker_instance
from app.models.admin import Admin
from app.models.location import Location
from app.utilities.geocoding import geocode_addresses


async def _get_archive_threshold(session) -> int:
    """Get the route archive threshold from admin settings"""
    logger = get_logger()
    statement = select(Admin)
    result = await session.execute(statement)
    admin_record = result.scalars().first()

    if not admin_record:
        logger.warning("No admin record found, using default threshold of 30 days")
        return 30

    threshold = admin_record.route_archive_after or 30
    logger.info(f"Using route_archive_after threshold: {threshold} days")
    return threshold


async def _get_locations_to_refresh(session, cutoff_date) -> list[Location]:
    """Query locations that need geocoding refresh"""
    logger = get_logger()
    statement = select(Location).where(
        or_(
            Location.geocoded_at.is_(None),
            Location.geocoded_at < cutoff_date
        )
    )
    result = await session.execute(statement)
    locations = result.scalars().all()
    logger.info(f"Found {len(locations)} locations to refresh")
    return locations


async def _refresh_locations(session, locations: list[Location]) -> int:
    """Batch geocode and update locations, returns count of successfully refreshed"""
    logger = get_logger()

    if not locations:
        logger.info("No locations need geocoding refresh")
        return 0

    addresses = [loc.address for loc in locations]
    geocoding_results = await geocode_addresses(addresses)

    refreshed_count = 0
    for location, coords in zip(locations, geocoding_results):
        if coords:
            location.latitude = coords["lat"]
            location.longitude = coords["lng"]
            location.geocoded_at = datetime.now()
            refreshed_count += 1
            logger.info(
                f"Refreshed geocoding for location {location.location_id} "
                f"({location.address}): {coords}"
            )
        else:
            logger.warning(
                f"Failed to geocode location {location.location_id} "
                f"({location.address})"
            )

    await session.commit()
    logger.info(f"Successfully refreshed {refreshed_count}/{len(locations)} locations")
    return refreshed_count


async def refresh_geocoding() -> None:
    """Refresh geocoding for locations - runs daily

    This job:
    1. Gets the route_archive_after setting from admin_info (default 30 days)
    2. Finds all locations that need refreshing (geocoded_at is null or older than threshold)
    3. Refreshes lat/lon for those locations using Google Geocoding API
    4. Updates geocoded_at timestamp for refreshed locations
    """
    logger = get_logger()

    if async_session_maker_instance is None:
        logger.error("Database session maker not initialized")
        return

    try:
        async with async_session_maker_instance() as session:
            admin_statement = select(Admin)
            admin_result = await session.execute(admin_statement)
            admin_record = admin_result.scalars().first()

            archive_threshold_days = await _get_archive_threshold(session)
            cutoff_date = datetime.now() - timedelta(days=archive_threshold_days)

            locations = await _get_locations_to_refresh(session, cutoff_date)
            await _refresh_locations(session, locations)

    except Exception as error:
        logger.error(
            f"Failed to refresh geocoding: {error!s}", exc_info=True
        )
        raise error

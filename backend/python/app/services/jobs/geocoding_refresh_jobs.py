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
from app.utilities.geocoding import geocode, geocode_addresses


async def refresh_geocoding() -> None:
    """Refresh geocoding for locations and warehouse - runs daily

    This job:
    1. Gets the route_archive_after setting from admin_info (default 30 days)
    2. Finds all locations that need refreshing (geocoded_at is null or older than threshold)
    3. Refreshes lat/lon for those locations using Google Geocoding API
    4. Updates geocoded_at timestamp for refreshed locations
    5. Refreshes the warehouse location in admin_info table
    """
    logger = get_logger()

    if async_session_maker_instance is None:
        logger.error("Database session maker not initialized")
        return

    try:
        async with async_session_maker_instance() as session:
            # Get the admin settings to determine archive threshold
            admin_statement = select(Admin)
            admin_result = await session.execute(admin_statement)
            admin_record = admin_result.scalars().first()

            if not admin_record:
                logger.warning("No admin record found, using default threshold of 30 days")
                archive_threshold_days = 30
            else:
                archive_threshold_days = admin_record.route_archive_after or 30
                logger.info(f"Using route_archive_after threshold: {archive_threshold_days} days")

            # Calculate the cutoff date
            cutoff_date = datetime.now() - timedelta(days=archive_threshold_days)

            # Find all locations that need refreshing
            # (geocoded_at is null OR geocoded_at < cutoff_date)
            location_statement = select(Location).where(
                or_(
                    Location.geocoded_at.is_(None),
                    Location.geocoded_at < cutoff_date
                )
            )
            location_result = await session.execute(location_statement)
            locations_to_refresh = location_result.scalars().all()

            if not locations_to_refresh:
                logger.info("No locations need geocoding refresh")
            else:
                logger.info(f"Found {len(locations_to_refresh)} locations to refresh")

                # Collect addresses and their corresponding location IDs
                addresses = [loc.address for loc in locations_to_refresh]

                # Batch geocode all addresses
                geocoding_results = await geocode_addresses(addresses)

                # Update each location with new coordinates
                refreshed_count = 0
                for location, coords in zip(locations_to_refresh, geocoding_results):
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
                logger.info(f"Successfully refreshed {refreshed_count}/{len(locations_to_refresh)} locations")

            # Refresh warehouse location if it exists
            if admin_record and admin_record.warehouse_location:
                logger.info("Refreshing warehouse location geocoding")
                warehouse_coords = await geocode(admin_record.warehouse_location)

                if warehouse_coords:
                    # Store warehouse coordinates in a separate table or add fields to admin
                    # For now, we'll just log it since admin table doesn't have lat/lng fields
                    logger.info(
                        f"Warehouse location geocoded: {admin_record.warehouse_location} -> {warehouse_coords}"
                    )
                    # TODO: Add warehouse_latitude and warehouse_longitude fields to admin table if needed
                else:
                    logger.warning(
                        f"Failed to geocode warehouse location: {admin_record.warehouse_location}"
                    )

    except Exception as error:
        logger.error(
            f"Failed to refresh geocoding: {error!s}", exc_info=True
        )
        raise error

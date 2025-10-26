#!/usr/bin/env python3
"""
Simple script to test database connection and show route groups
"""

import os
import asyncio
from datetime import datetime
from typing import List

# Add environment variables for testing
os.environ["DATABASE_URL"] = "sqlite:///./test.db"  # Adjust if needed

try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlmodel import select
    from app.models.route_group import RouteGroup
    from app.models import get_database_url

    async def test_route_groups():
        """Test database connection and show route groups"""
        try:
            # Get database URL
            db_url = get_database_url()
            print(f"Using database URL: {db_url}")

            # Create async engine
            engine = create_async_engine(db_url, echo=True)

            # Create session
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

            async with async_session() as session:
                # Query route groups
                statement = select(RouteGroup)
                result = await session.execute(statement)
                route_groups = result.scalars().all()

                print(f"\nFound {len(route_groups)} route groups:")
                print("=" * 80)

                for rg in route_groups:
                    print(f"ID: {rg.route_group_id}")
                    print(f"Name: {rg.name}")
                    print(f"Drive Date: {rg.drive_date}")
                    print(f"Notes: {rg.notes}")
                    print(f"Number of Routes: {len(rg.route_group_memberships) if hasattr(rg, 'route_group_memberships') else 'Unknown'}")
                    print("-" * 40)

                if len(route_groups) == 0:
                    print("No route groups found in database.")
                    print("Let's create a sample route group...")

                    # Create a sample route group
                    sample_rg = RouteGroup(
                        name="Sample Morning Route",
                        notes="This is a sample route group for testing",
                        drive_date=datetime.now()
                    )

                    session.add(sample_rg)
                    await session.commit()
                    await session.refresh(sample_rg)

                    print(f"Created sample route group: {sample_rg.name} (ID: {sample_rg.route_group_id})")

            await engine.dispose()

        except Exception as e:
            print(f"Error: {e}")
            print("Please check your database configuration.")

    if __name__ == "__main__":
        asyncio.run(test_route_groups())

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're in the backend/python directory and dependencies are installed.")
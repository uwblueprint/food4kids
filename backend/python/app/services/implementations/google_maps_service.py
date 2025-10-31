import json
import httpx

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.models.admin import Admin
import datetime

class RouteGenerationSettings(SQLModel):
    """Settings for route generation.

    These are not persisted to the database; used as inputs to services.
    """

    return_to_warehouse: bool = False
    route_start_time: datetime
    num_routes: int


class RouteGenerationGroupInput(SQLModel):
    """Input bundle for a single location group route generation."""

    location_group: LocationGroup
    settings: RouteGenerationSettings



async def generate_route_groups(
        self, session: AsyncSession, group_inputs: list[RouteGenerationGroupInput]
    ) -> list[RouteGroup]:
    warehouse = 
    for route_generation_group in group_inputs:
        location_group = route_generation_group.locations
        for location in location_group:
            
    '''
    {
      "model": {
        "shipments": [
          {
            "pickups": [
              {
                "arrivalLocation": {
                  "latitude": 37.73881799999999,
                  "longitude": -122.4161
                }
              }
            ],
            "deliveries": [
              {
                "arrivalLocation": {
                  "latitude": 37.79581,
                  "longitude": -122.4218856
                }
              }
            ]
          }
        ],
        "vehicles": [
          {
            "startLocation": {
              "latitude": 37.73881799999999,
              "longitude": -122.4161
            },
            "endLocation": {
              "latitude": 37.73881799999999,
              "longitude": -122.4161
            },
            "costPerKilometer": 1.0
          }
        ],
      "globalStartTime": "2024-02-13T00:00:00.000Z",
      "globalEndTime": "2024-02-14T06:00:00.000Z"
      }
    }
    '''
    return


# one way of doing things

# app/models/generation_types.py
from uuid import UUID

from pydantic import BaseModel

# class AlgorithmOptions(BaseModel):
#     engine: Literal["ortools", "heuristic"] = "ortools"
#     seed: Optional[int] = None


class RouteGenerationRequest(BaseModel):
    route_group_id: UUID
    # options: AlgorithmOptions = AlgorithmOptions()

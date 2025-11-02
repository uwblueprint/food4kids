# 

# app/models/generation_types.py
from pydantic import BaseModel
from uuid import UUID

# class AlgorithmOptions(BaseModel):
#     engine: Literal["ortools", "heuristic"] = "ortools"
#     seed: Optional[int] = None

class RouteGenerationRequest(BaseModel):
    route_group_id: UUID
    # options: AlgorithmOptions = AlgorithmOptions()
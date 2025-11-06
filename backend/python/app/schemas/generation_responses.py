from uuid import UUID

from sqlmodel import SQLModel


class JobEnqueueResponse(SQLModel):
    """Job creation response"""

    job_id: UUID

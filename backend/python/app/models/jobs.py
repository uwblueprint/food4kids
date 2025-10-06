from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from .base import BaseModel
from .enum import ProgressEnum


class JobsBase(SQLModel):
    """Shared fields between table and API models"""

    route_group_id: UUID | None = Field(foreign_key="route_groups.id")
    progress: ProgressEnum = Field(default=ProgressEnum.PENDING)


class Jobs(JobsBase, BaseModel, table=True):
    """Jobs model for demonstration purposes"""

    __tablename__ = "jobs"

    job_id: UUID = Field(default_factory=uuid4, primary_key=True)
    started_at: datetime | None = Field(
        default_factory=datetime.utcnow,
    )
    updated_at: datetime | None = Field(
        default=None,
    )
    finished_at: datetime | None = Field(
        default=None,
    )


class JobsCreate(JobsBase):
    """Jobs creation request"""

    pass


class JobsRead(JobsBase):
    """Jobs response model"""

    jobs_id: UUID
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class JobsUpdate(SQLModel):
    """Jobs update request - all optional"""

    progress: str | None = None
    route_group_id: UUID | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

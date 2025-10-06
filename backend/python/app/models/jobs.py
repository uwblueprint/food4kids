from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from .base import BaseModel
from .enum import StatusEnum


class JobsBase(SQLModel):
    """Shared fields between table and API models"""

    route_group_id: UUID | None = Field(foreign_key="route_groups.id")
    status: StatusEnum = Field(default=StatusEnum.PENDING)
    progress: str = Field(default=None)


class Jobs(JobsBase, BaseModel, table=True):
    """Jobs model for demonstration purposes"""

    __tablename__ = "jobs"

    jobs_id: UUID = Field(default_factory=uuid4, primary_key=True)
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

    status: StatusEnum | None = None
    progress: str | None = None
    route_group_id: UUID | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

from .enum import StatusEnum
from .base import BaseModel
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import DateTime
from datetime import datetime
from sqlmodel import SQLModel, Field


class JobsBase(SQLModel):
    """Shared fields between table and API models"""

    route_group_id: Optional[UUID] = Field(foreign_key="route_groups.id")
    status: StatusEnum = Field(default=StatusEnum.PENDING)
    progress: str = Field(default=None)


class Jobs(JobsBase, BaseModel, table=True):
    __tablename__ = "jobs"

    id: UUID = Field(default=uuid4, primary_key=True)
    started_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_type=DateTime(timezone=True),
        description="Timestamp when the record was created",
    )
    finished_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        description="Timestamp when the record is finished",
    )


class JobsCreate(JobsBase):
    pass


class JobsRead(JobsBase):
    id: UUID
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class JobsUpdate(SQLModel):
    status: Optional[StatusEnum] = None
    progress: Optional[str] = None
    route_group_id: Optional[UUID] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

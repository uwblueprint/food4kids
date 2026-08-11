from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime, Text
from sqlmodel import Field, SQLModel

from .base import BaseModel
from .enum import ProgressEnum


class JobBase(SQLModel):
    """Shared fields between table and API models"""

    route_group_id: UUID | None = Field(
        default=None, foreign_key="route_groups.route_group_id"
    )
    progress: ProgressEnum = Field(default=ProgressEnum.PENDING)


class Job(JobBase, BaseModel, table=True):
    """Job model for demonstration purposes"""

    __tablename__ = "jobs"

    job_id: UUID = Field(default_factory=uuid4, primary_key=True)
    # The job lifecycle timestamps are `timestamptz` holding UTC, like every
    # other timestamp in the schema. They start null and are stamped as the job
    # moves through Pending → Running → Completed/Failed.
    started_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    updated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    finished_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    input_payload: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    error_message: str | None = Field(default=None, sa_type=Text)
    retry_count: int = Field(default=0)
    routes_created: int | None = Field(default=None)
    total_stops: int | None = Field(default=None)
    total_distance_km: float | None = Field(default=None)
    total_families: int | None = Field(default=None)


class JobCreate(JobBase):
    """Job creation request"""

    pass


class JobRead(JobBase):
    """Job response model"""

    job_id: UUID
    error_message: str | None = None
    routes_created: int | None = None
    total_stops: int | None = None
    total_distance_km: float | None = None
    total_families: int | None = None


class JobUpdate(SQLModel):
    """Job update request - all optional"""

    progress: ProgressEnum | None = None
    route_group_id: UUID | None = None
    started_at: datetime | None = None
    updated_at: datetime | None = None
    finished_at: datetime | None = None

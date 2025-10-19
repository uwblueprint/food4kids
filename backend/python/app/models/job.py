from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from .base import BaseModel
from .enum import ProgressEnum


class JobBase(SQLModel):
    """Shared fields between table and API models"""

<<<<<<< HEAD
<<<<<<< HEAD
    route_group_id: UUID | None = Field(
        default=None, foreign_key="route_groups.route_group_id"
    )
=======
    route_group_id: UUID | None = Field(foreign_key="route_groups.route_group_id")
>>>>>>> 27f9f91 (Fix job import)
=======
    route_group_id: UUID | None = Field(foreign_key="route_groups.route_group_id")
>>>>>>> 60cc40f1582d3e202aafec387e2306bfd622a8a6
    progress: ProgressEnum = Field(default=ProgressEnum.PENDING)


class Job(JobBase, BaseModel, table=True):
    """Job model for demonstration purposes"""

<<<<<<< HEAD
<<<<<<< HEAD
    __tablename__ = "jobs"
=======
    __tablename__ = "job"
>>>>>>> 27f9f91 (Fix job import)
=======
    __tablename__ = "job"
>>>>>>> 60cc40f1582d3e202aafec387e2306bfd622a8a6

    job_id: UUID = Field(default_factory=uuid4, primary_key=True)
    started_at: datetime | None = Field(
        default=None,
    )
    updated_at: datetime | None = Field(
        default=None,
    )
    finished_at: datetime | None = Field(
        default=None,
    )


class JobCreate(JobBase):
    """Job creation request"""

    pass


class JobRead(JobBase):
    """Job response model"""

    job_id: UUID


class JobUpdate(SQLModel):
    """Job update request - all optional"""

    progress: ProgressEnum | None = None
    route_group_id: UUID | None = None
    started_at: datetime | None = None
    updated_at: datetime | None = None
    finished_at: datetime | None = None

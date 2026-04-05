from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from .base import BaseModel


class AnnouncementLastRead(BaseModel, table=True):
    """Tracks when each user last viewed the announcements page"""

    __tablename__ = "announcement_last_reads"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_announcement_last_reads_user"),
    )

    announcement_last_read_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(
        foreign_key="users.user_id", nullable=False, ondelete="CASCADE"
    )
    last_read_at: datetime = Field(nullable=False)


class AnnouncementLastReadResponse(SQLModel):
    """Response model for announcement last read"""

    model_config = {"from_attributes": True}

    announcement_last_read_id: UUID
    user_id: UUID
    last_read_at: datetime


class MarkReadRequest(SQLModel):
    """Request body for marking announcements as read"""

    user_id: UUID

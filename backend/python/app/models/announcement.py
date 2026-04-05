from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Text
from sqlmodel import Column, Field, Relationship, SQLModel

from .base import BaseModel
from .user import User


class AnnouncementBase(SQLModel):
    """Shared fields between table and API models"""

    subject: str = Field(min_length=1, max_length=255)
    message: str = Field(sa_column=Column(Text, nullable=False))


class Announcement(AnnouncementBase, BaseModel, table=True):
    """Announcement model - separate from note chains, includes subject field"""

    __tablename__ = "announcements"

    announcement_id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(
        foreign_key="users.user_id", nullable=False, ondelete="CASCADE"
    )
    attachments: list[str] = Field(
        default_factory=list, sa_column=Column(JSON, default=[])
    )

    user: User = Relationship()


class AnnouncementCreate(AnnouncementBase):
    """Announcement creation request"""

    user_id: UUID
    attachments: list[str] = Field(default_factory=list)


class AnnouncementRead(AnnouncementBase):
    """Announcement response model"""

    model_config = {"from_attributes": True}

    announcement_id: UUID
    user_id: UUID
    attachments: list[str]
    created_at: datetime | None
    updated_at: datetime | None
    is_read: bool | None = None


class AnnouncementUpdate(SQLModel):
    """Announcement update request - all optional"""

    subject: str | None = Field(default=None, min_length=1, max_length=255)
    message: str | None = Field(default=None)
    attachments: list[str] | None = Field(default=None)

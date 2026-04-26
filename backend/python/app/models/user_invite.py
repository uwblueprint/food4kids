from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

from app.models.user import User

from .base import BaseModel


class UserInviteBase(SQLModel):
    user_id: UUID = Field(foreign_key="users.user_id", index=True, unique=True)
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=2),
    )
    is_used: bool = Field(default=False)


class UserInvite(UserInviteBase, BaseModel, table=True):
    __tablename__ = "user_invites"

    user_invite_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user: User = Relationship()


class UserInviteCreate(SQLModel):
    user_id: UUID

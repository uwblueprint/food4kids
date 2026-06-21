from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

from app.models.user import User

from .base import BaseModel

PASSWORD_RESET_TOKEN_EXPIRY_DAYS = 1

class PasswordResetTokenBase(SQLModel):
    user_id: UUID = Field(
        foreign_key="users.user_id", index=True, unique=True, ondelete="CASCADE"
    )
    token_hash: str = Field(nullable=False, index=True)     
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=PASSWORD_RESET_TOKEN_EXPIRY_DAYS),
    )
    is_used: bool = Field(default=False)


class PasswordResetToken(PasswordResetTokenBase, BaseModel, table=True):
    __tablename__ = "password_reset_tokens"

    password_reset_token_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user: User = Relationship()


class PasswordResetTokenCreate(SQLModel):
    user_id: UUID
    token_hash: str

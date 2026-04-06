from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlmodel import Column, Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .note_chain import NoteChain


class Attachment(SQLModel):
    """Attachment with filename and URL"""

    filename: str
    url: str


class NoteBase(SQLModel):
    """Shared fields between table and API models"""

    note_chain_id: UUID = Field(foreign_key="note_chains.note_chain_id", nullable=False)
    user_id: UUID | None = Field(
        default=None, foreign_key="users.user_id", nullable=True
    )
    message: str = Field(min_length=1, max_length=2000)
    is_system: bool = Field(default=False)
    attachments: list[Attachment] = Field(
        default=[], sa_column=Column(sa.JSON, nullable=True, default=[])
    )


class Note(NoteBase, BaseModel, table=True):
    """Database table model for individual notes (comments)"""

    __tablename__ = "notes"

    note_id: UUID = Field(default_factory=uuid4, primary_key=True)

    note_chain: "NoteChain" = Relationship(back_populates="notes")


class NoteCreate(SQLModel):
    """Create request model - chain_id and user_id set by the service"""

    message: str = Field(min_length=1, max_length=2000)
    attachments: list[Attachment] = Field(default=[])


class NoteRead(NoteBase):
    """Read response model"""

    note_id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None


class NoteUpdate(SQLModel):
    """Update request model - only message can be edited"""

    message: str = Field(min_length=1, max_length=2000)

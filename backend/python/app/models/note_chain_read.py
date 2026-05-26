from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from .base import BaseModel


class NoteChainReadBase(SQLModel):
    """Shared fields between table and API models"""

    note_chain_id: UUID = Field(foreign_key="note_chains.note_chain_id", nullable=False)
    user_id: UUID = Field(foreign_key="users.user_id", nullable=False)
    last_read_at: datetime = Field(nullable=False)


class NoteChainReadModel(NoteChainReadBase, BaseModel, table=True):
    """Database table model for tracking how far each user has read a note chain"""

    __tablename__ = "note_chain_reads"
    __table_args__ = (
        UniqueConstraint(
            "note_chain_id", "user_id", name="uq_note_chain_reads_chain_user"
        ),
    )
    note_chain_read_id: UUID = Field(default_factory=uuid4, primary_key=True)


class NoteChainReadResponse(NoteChainReadBase):
    """Read response model"""

    note_chain_read_id: UUID

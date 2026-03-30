from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel
from .enum import NotePermission

if TYPE_CHECKING:
    from .note import Note


class NoteChainBase(SQLModel):
    """Shared fields between table and API models"""

    read_permission: NotePermission = Field(default=NotePermission.ADMIN)
    write_permission: NotePermission = Field(default=NotePermission.ADMIN)


class NoteChain(NoteChainBase, BaseModel, table=True):
    """Database table model for note chains (comment sections)"""

    __tablename__ = "note_chains"

    note_chain_id: UUID = Field(default_factory=uuid4, primary_key=True)

    notes: list["Note"] = Relationship(
        back_populates="note_chain",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class NoteChainCreate(NoteChainBase):
    """Create request model"""

    pass


class NoteChainRead(NoteChainBase):
    """Read response model"""

    note_chain_id: UUID



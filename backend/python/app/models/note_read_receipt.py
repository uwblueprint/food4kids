from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel

from app.utilities.datetime_utils import now_utc

from .base import UTCDateTime


class NoteReadReceipt(SQLModel, table=True):
    """An admin's last viewing of an individual location note."""

    __tablename__ = "note_read_receipts"

    user_id: UUID = Field(
        foreign_key="users.user_id", primary_key=True, ondelete="CASCADE"
    )
    note_id: UUID = Field(
        foreign_key="notes.note_id", primary_key=True, ondelete="CASCADE"
    )
    read_at: datetime = Field(default_factory=now_utc, sa_type=UTCDateTime)

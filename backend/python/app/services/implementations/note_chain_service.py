import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, func, select

from app.models.enum import NotePermission
from app.models.note import Note, NoteCreate, NoteUpdate
from app.models.note_chain import NoteChain, NoteChainCreate, NoteChainUpdate
from app.models.note_chain_read import NoteChainReadModel
from app.models.user import User


class NoteChainService:
    """Service for managing note chains (comment sections) and their notes"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def _get_user_role(self, session: AsyncSession, user_id: UUID) -> str | None:
        """Get the role of a user by their ID"""
        statement = select(User.role).where(User.user_id == user_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    def _check_permission(self, permission: str, user_role: str | None) -> bool:
        """Check if a user role satisfies a permission level"""
        if permission == NotePermission.ALL:
            return True
        if permission == NotePermission.ADMIN:
            return user_role is not None and user_role.lower() == "admin"
        return False

    # --- Note Chain CRUD ---

    async def create_note_chain(
        self, session: AsyncSession, data: NoteChainCreate
    ) -> NoteChain:
        """Create a new note chain"""
        try:
            note_chain = NoteChain(
                read_permission=data.read_permission,
                write_permission=data.write_permission,
            )
            session.add(note_chain)
            await session.commit()
            await session.refresh(note_chain)
            return note_chain
        except Exception as e:
            self.logger.error(f"Failed to create note chain: {e!s}")
            await session.rollback()
            raise e

    async def get_note_chain_by_id(
        self, session: AsyncSession, note_chain_id: UUID
    ) -> NoteChain:
        """Get a note chain by ID"""
        try:
            statement = select(NoteChain).where(
                NoteChain.note_chain_id == note_chain_id
            )
            result = await session.execute(statement)
            note_chain = result.scalars().first()

            if not note_chain:
                raise ValueError(f"Note chain with id {note_chain_id} not found")

            return note_chain
        except Exception as e:
            self.logger.error(f"Failed to get note chain by id: {e!s}")
            raise e

    async def update_note_chain(
        self,
        session: AsyncSession,
        note_chain_id: UUID,
        data: NoteChainUpdate,
        user_id: UUID,
    ) -> NoteChain:
        """Update a note chain's permissions (admin only)"""
        try:
            user_role = await self._get_user_role(session, user_id)
            if not user_role or user_role.lower() != "admin":
                raise PermissionError("Only admins can update note chain permissions")

            note_chain = await self.get_note_chain_by_id(session, note_chain_id)
            updated_data = data.model_dump(exclude_unset=True)
            for field, value in updated_data.items():
                setattr(note_chain, field, value)

            await session.commit()
            await session.refresh(note_chain)
            return note_chain
        except Exception as e:
            self.logger.error(f"Failed to update note chain: {e!s}")
            await session.rollback()
            raise e

    async def delete_note_chain(
        self, session: AsyncSession, note_chain_id: UUID, user_id: UUID
    ) -> None:
        """Delete a note chain and all its notes (admin only)"""
        try:
            user_role = await self._get_user_role(session, user_id)
            if not user_role or user_role.lower() != "admin":
                raise PermissionError("Only admins can delete note chains")

            note_chain = await self.get_note_chain_by_id(session, note_chain_id)

            # Delete associated read tracking entries
            read_statement = select(NoteChainReadModel).where(
                NoteChainReadModel.note_chain_id == note_chain_id
            )
            read_result = await session.execute(read_statement)
            for read_entry in read_result.scalars().all():
                await session.delete(read_entry)

            await session.delete(note_chain)
            await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to delete note chain: {e!s}")
            await session.rollback()
            raise e

    # --- Notes CRUD ---

    async def get_notes_by_chain_id(
        self,
        session: AsyncSession,
        note_chain_id: UUID,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Note]:
        """Get notes for a chain with pagination, ordered by created_at ascending"""
        try:
            # Verify chain exists and check read permission
            note_chain = await self.get_note_chain_by_id(session, note_chain_id)
            user_role = await self._get_user_role(session, user_id)

            if not self._check_permission(note_chain.read_permission, user_role):
                raise PermissionError(
                    "You do not have permission to read this note chain"
                )

            statement = (
                select(Note)
                .where(Note.note_chain_id == note_chain_id)
                .order_by(col(Note.created_at).asc())
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(statement)
            return list(result.scalars().all())
        except Exception as e:
            self.logger.error(f"Failed to get notes by chain id: {e!s}")
            raise e

    async def create_note(
        self,
        session: AsyncSession,
        note_chain_id: UUID,
        user_id: UUID | None,
        data: NoteCreate,
        is_system: bool = False,
    ) -> Note:
        """Add a note to a chain. user_id=None for system notes."""
        try:
            note_chain = await self.get_note_chain_by_id(session, note_chain_id)

            # Check write permission (system notes bypass permission check)
            if not is_system and user_id is not None:
                user_role = await self._get_user_role(session, user_id)
                if not self._check_permission(note_chain.write_permission, user_role):
                    raise PermissionError(
                        "You do not have permission to write to this note chain"
                    )

            note = Note(
                note_chain_id=note_chain_id,
                user_id=user_id,
                message=data.message,
                is_system=is_system,
            )
            session.add(note)
            await session.commit()
            await session.refresh(note)
            return note
        except Exception as e:
            self.logger.error(f"Failed to create note: {e!s}")
            await session.rollback()
            raise e

    async def get_note_by_id(self, session: AsyncSession, note_id: UUID) -> Note:
        """Get a single note by ID"""
        try:
            statement = select(Note).where(Note.note_id == note_id)
            result = await session.execute(statement)
            note = result.scalars().first()

            if not note:
                raise ValueError(f"Note with id {note_id} not found")

            return note
        except Exception as e:
            self.logger.error(f"Failed to get note by id: {e!s}")
            raise e

    async def update_note(
        self,
        session: AsyncSession,
        note_chain_id: UUID,
        note_id: UUID,
        user_id: UUID,
        data: NoteUpdate,
    ) -> Note:
        """Update a note's message. Only the author or an admin can edit."""
        try:
            note = await self.get_note_by_id(session, note_id)
            if note.note_chain_id != note_chain_id:
                raise ValueError(
                    f"Note {note_id} does not belong to chain {note_chain_id}"
                )
            user_role = await self._get_user_role(session, user_id)

            is_author = note.user_id == user_id
            is_admin = user_role is not None and user_role.lower() == "admin"

            if not (is_author or is_admin):
                raise PermissionError("Only the author or an admin can edit this note")

            note.message = data.message
            await session.commit()
            await session.refresh(note)
            return note
        except Exception as e:
            self.logger.error(f"Failed to update note: {e!s}")
            await session.rollback()
            raise e

    async def delete_note(
        self, session: AsyncSession, note_chain_id: UUID, note_id: UUID, user_id: UUID
    ) -> None:
        """Delete a note. Only the author or an admin can delete."""
        try:
            note = await self.get_note_by_id(session, note_id)
            if note.note_chain_id != note_chain_id:
                raise ValueError(
                    f"Note {note_id} does not belong to chain {note_chain_id}"
                )
            user_role = await self._get_user_role(session, user_id)

            is_author = note.user_id == user_id
            is_admin = user_role is not None and user_role.lower() == "admin"

            if not (is_author or is_admin):
                raise PermissionError(
                    "Only the author or an admin can delete this note"
                )

            await session.delete(note)
            await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to delete note: {e!s}")
            await session.rollback()
            raise e

    # --- Read Tracking ---

    async def mark_chain_as_read(
        self, session: AsyncSession, note_chain_id: UUID, user_id: UUID
    ) -> NoteChainReadModel:
        """Mark a note chain as read by upserting last_read_at to now"""
        try:
            # Verify chain exists
            await self.get_note_chain_by_id(session, note_chain_id)

            # Check if a read entry already exists
            statement = select(NoteChainReadModel).where(
                NoteChainReadModel.note_chain_id == note_chain_id,
                NoteChainReadModel.user_id == user_id,
            )
            result = await session.execute(statement)
            read_entry = result.scalars().first()

            now = datetime.now(timezone.utc).replace(tzinfo=None)

            if read_entry:
                read_entry.last_read_at = now
                read_entry.updated_at = now
            else:
                read_entry = NoteChainReadModel(
                    note_chain_id=note_chain_id,
                    user_id=user_id,
                    last_read_at=now,
                )
                session.add(read_entry)

            await session.commit()
            await session.refresh(read_entry)
            return read_entry
        except Exception as e:
            self.logger.error(f"Failed to mark chain as read: {e!s}")
            await session.rollback()
            raise e

    async def get_unread_count(
        self, session: AsyncSession, note_chain_id: UUID, user_id: UUID
    ) -> int:
        """Get the count of unread notes in a chain for a user"""
        try:
            # Verify chain exists
            await self.get_note_chain_by_id(session, note_chain_id)

            # Get last read time
            read_statement = select(NoteChainReadModel.last_read_at).where(
                NoteChainReadModel.note_chain_id == note_chain_id,
                NoteChainReadModel.user_id == user_id,
            )
            read_result = await session.execute(read_statement)
            last_read_at = read_result.scalar_one_or_none()

            # Count notes after last_read_at (or all notes if never read)
            count_statement = select(func.count(col(Note.note_id))).where(
                Note.note_chain_id == note_chain_id
            )
            if last_read_at is not None:
                count_statement = count_statement.where(
                    col(Note.created_at) > last_read_at
                )

            count_result = await session.execute(count_statement)
            return count_result.scalar_one()
        except Exception as e:
            self.logger.error(f"Failed to get unread count: {e!s}")
            raise e

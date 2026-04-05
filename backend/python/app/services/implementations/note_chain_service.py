import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select, update

from app.models.enum import NotePermission
from app.models.location import Location
from app.models.note import Note, NoteCreate, NoteUpdate
from app.models.note_chain import NoteChain, NoteChainCreate
from app.models.route import Route
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

    async def get_note_chain_with_permission(
        self, session: AsyncSession, note_chain_id: UUID, user_id: UUID
    ) -> NoteChain:
        """Get a note chain by ID, checking read permission"""
        try:
            note_chain = await self.get_note_chain_by_id(session, note_chain_id)
            user_role = await self._get_user_role(session, user_id)

            if not self._check_permission(note_chain.read_permission, user_role):
                raise PermissionError(
                    "You do not have permission to read this note chain"
                )

            return note_chain
        except Exception as e:
            self.logger.error(f"Failed to get note chain with permission: {e!s}")
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

            # Null out FK references on locations and routes
            await session.execute(
                update(Location)
                .where(col(Location.note_chain_id) == note_chain_id)
                .values(note_chain_id=None)
            )
            await session.execute(
                update(Route)
                .where(col(Route.note_chain_id) == note_chain_id)
                .values(note_chain_id=None)
            )

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
                attachments=data.attachments,
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


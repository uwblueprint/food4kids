import firebase_admin.auth
import logging
from typing import List, Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.user import User, UserCreate, UserUpdate, UserRead
from ..interfaces.user_service import IUserService


class UserService(IUserService):
    """Modern FastAPI-style user service"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    async def get_user_by_id(self, session: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID - returns SQLModel instance"""
        try:
            statement = select(User).where(User.id == user_id)
            result = await session.execute(statement)
            user = result.scalars().first()

            if not user:
                self.logger.error(f"User with id {user_id} not found")
                return None

            return user
        except Exception as e:
            self.logger.error(f"Failed to get user by id: {str(e)}")
            raise e

    async def get_user_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        """Get user by email using Firebase"""
        try:
            firebase_user = firebase_admin.auth.get_user_by_email(email)
            statement = select(User).where(User.auth_id == firebase_user.uid)
            result = await session.execute(statement)
            user = result.scalars().first()

            if not user:
                self.logger.error(f"User with email {email} not found")
                return None

            return user
        except Exception as e:
            self.logger.error(f"Failed to get user by email: {str(e)}")
            raise e

    async def get_users(self, session: AsyncSession) -> List[User]:
        """Get all users - returns SQLModel instances"""
        try:
            statement = select(User)
            result = await session.execute(statement)
            return result.scalars().all()
        except Exception as e:
            self.logger.error(f"Failed to get users: {str(e)}")
            raise e

    async def create_user(self, session: AsyncSession, user_data: UserCreate, auth_id: Optional[str] = None, signup_method: str = "PASSWORD") -> User:
        """Create new user with Firebase integration"""
        firebase_user = None
        
        try:
            # Create Firebase user
            if signup_method == "PASSWORD":
                firebase_user = firebase_admin.auth.create_user(
                    email=user_data.email, password=user_data.password
                )
            elif signup_method == "GOOGLE":
                firebase_user = firebase_admin.auth.get_user(uid=auth_id)

            # Create database user
            user = User(
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                email=user_data.email,
                auth_id=firebase_user.uid,
                role=user_data.role,
            )

            try:
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user
                
            except Exception as db_error:
                # Rollback Firebase user creation
                try:
                    firebase_admin.auth.delete_user(firebase_user.uid)
                except Exception as firebase_error:
                    self.logger.error(f"Failed to rollback Firebase user: {str(firebase_error)}")
                raise db_error

        except Exception as e:
            self.logger.error(f"Failed to create user: {str(e)}")
            raise e

    async def update_user_by_id(self, session: AsyncSession, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user by ID"""
        try:
            statement = select(User).where(User.id == user_id)
            result = await session.execute(statement)
            user = result.scalars().first()

            if not user:
                self.logger.error(f"User with id {user_id} not found")
                return None

            # Store old values for rollback
            old_first_name = user.first_name
            old_last_name = user.last_name
            old_role = user.role

            # Update user fields
            user.first_name = user_data.first_name
            user.last_name = user_data.last_name
            user.role = user_data.role

            await session.commit()

            # Update Firebase email
            try:
                firebase_admin.auth.update_user(user.auth_id, email=user_data.email)
                await session.refresh(user)
                return user
                
            except Exception as firebase_error:
                # Rollback database changes
                user.first_name = old_first_name
                user.last_name = old_last_name
                user.role = old_role
                await session.commit()
                raise firebase_error

        except Exception as e:
            self.logger.error(f"Failed to update user: {str(e)}")
            raise e

    async def delete_user_by_id(self, session: AsyncSession, user_id: int) -> bool:
        """Delete user by ID"""
        try:
            statement = select(User).where(User.id == user_id)
            result = await session.execute(statement)
            user = result.scalars().first()

            if not user:
                self.logger.error(f"User with id {user_id} not found")
                return False

            # Store for rollback
            user_data = {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "auth_id": user.auth_id,
                "role": user.role,
            }

            await session.delete(user)
            await session.commit()

            # Delete from Firebase
            try:
                firebase_admin.auth.delete_user(user.auth_id)
                return True
                
            except Exception as firebase_error:
                # Rollback database deletion
                new_user = User(**user_data)
                session.add(new_user)
                await session.commit()
                raise firebase_error

        except Exception as e:
            self.logger.error(f"Failed to delete user: {str(e)}")
            raise e

    async def get_user_role_by_auth_id(self, session: AsyncSession, auth_id: str) -> Optional[str]:
        """Get user role by auth_id"""
        try:
            statement = select(User).where(User.auth_id == auth_id)
            result = await session.execute(statement)
            user = result.scalars().first()
            
            if not user:
                return None
                
            # RoleEnum inherits from str, so user.role is already a string value
            return user.role
        except Exception as e:
            self.logger.error(f"Failed to get user role: {str(e)}")
            raise e

    async def get_auth_id_by_user_id(self, session: AsyncSession, user_id: int) -> Optional[str]:
        """Get auth_id by user_id"""
        try:
            statement = select(User).where(User.id == user_id)
            result = await session.execute(statement)
            user = result.scalars().first()
            
            if not user:
                self.logger.error(f"User with id {user_id} not found")
                return None
                
            return user.auth_id
        except Exception as e:
            self.logger.error(f"Failed to get auth_id by user_id: {str(e)}")
            raise e

    async def get_user_id_by_auth_id(self, session: AsyncSession, auth_id: str) -> Optional[int]:
        """Get user_id by auth_id"""
        try:
            statement = select(User).where(User.auth_id == auth_id)
            result = await session.execute(statement)
            user = result.scalars().first()
            
            if not user:
                self.logger.error(f"User with auth_id {auth_id} not found")
                return None
                
            return user.id
        except Exception as e:
            self.logger.error(f"Failed to get user_id by auth_id: {str(e)}")
            raise e

    async def delete_user_by_email(self, session: AsyncSession, email: str) -> bool:
        """Delete user by email"""
        try:
            firebase_user = firebase_admin.auth.get_user_by_email(email)
            statement = select(User).where(User.auth_id == firebase_user.uid)
            result = await session.execute(statement)
            user = result.scalars().first()

            if not user:
                self.logger.error(f"User with email {email} not found")
                return False

            # Store for rollback
            user_data = {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "auth_id": user.auth_id,
                "role": user.role,
            }

            await session.delete(user)
            await session.commit()

            # Delete from Firebase
            try:
                firebase_admin.auth.delete_user(user.auth_id)
                return True
                
            except Exception as firebase_error:
                # Rollback database deletion
                new_user = User(**user_data)
                session.add(new_user)
                await session.commit()
                raise firebase_error

        except Exception as e:
            self.logger.error(f"Failed to delete user by email: {str(e)}")
            raise e

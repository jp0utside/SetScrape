from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import joinedload
from datetime import datetime

from shared.database_models import User
from shared.models import (
    UserCreate, UserResponse, UserLogin, UserSession as UserSessionModel
)
from shared.auth import AuthUtils, session_manager

class UserService:
    """Service for user management operations"""
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_conditions = [User.username == user_data.username]
        if user_data.email:
            existing_conditions.append(User.email == user_data.email)
        
        existing_user = await db.execute(
            select(User).where(or_(*existing_conditions))
        )
        if existing_user.scalar_one_or_none():
            raise ValueError("Username or email already exists")
        
        # Hash password
        password_hash = AuthUtils.hash_password(user_data.password)
        
        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = await db.execute(
            select(User).where(User.username == username)
        )
        user = user.scalar_one_or_none()
        
        if user and AuthUtils.verify_password(password, user.password_hash):
            return user
        return None
    
    @staticmethod
    async def create_user_session(db: AsyncSession, user_id: str, username: str) -> UserSessionModel:
        """Create a new user session"""
        return await session_manager.create_session(user_id, username)
    
    @staticmethod
    async def invalidate_user_session(db: AsyncSession, user_id: str) -> bool:
        """Invalidate user session"""
        from shared.database_models import UserSession
        await db.execute(
            select(UserSession).where(UserSession.user_id == user_id).delete()
        )
        await db.commit()
        return True

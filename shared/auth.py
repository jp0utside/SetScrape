import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Union
from uuid import UUID
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import UserResponse, UserSession
from .database import get_db_session

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()

class AuthUtils:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

    @staticmethod
    def extract_user_id_from_token(token: str) -> UUID:
        """Extract user ID from JWT token"""
        payload = AuthUtils.verify_token(token)
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return UUID(user_id)

class AuthDependencies:
    @staticmethod
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """Get current user from JWT token"""
        token = credentials.credentials
        payload = AuthUtils.verify_token(token)
        
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return {
            "user_id": str(user_id),  # Return as string to match service expectations
            "username": payload.get("username"),
            "token_type": payload.get("type", "access")
        }

    @staticmethod
    async def get_current_user_optional(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Optional[dict]:
        """Get current user from JWT token (optional - returns None if not authenticated)"""
        try:
            token = credentials.credentials
            payload = AuthUtils.verify_token(token)
            
            user_id = payload.get("user_id")
            if user_id is None:
                return None
            
            return {
                "user_id": str(user_id),  # Return as string to match service expectations
                "username": payload.get("username"),
                "token_type": payload.get("type", "access")
            }
        except HTTPException:
            return None
        except Exception:
            return None

    @staticmethod
    async def get_current_active_user(
        current_user: dict = None
    ) -> dict:
        """Get current active user"""
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        return current_user

class SessionManager:
    def __init__(self):
        self.active_sessions = {}

    async def create_session(self, user_id: UUID, username: str) -> UserSession:
        """Create a new user session"""
        access_token = AuthUtils.create_access_token(
            data={"user_id": str(user_id), "username": username}
        )
        refresh_token = AuthUtils.create_refresh_token(
            data={"user_id": str(user_id), "username": username}
        )
        
        expires_at = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Store session
        self.active_sessions[access_token] = {
            "user_id": user_id,
            "username": username,
            "refresh_token": refresh_token,
            "expires_at": expires_at
        }
        
        return UserSession(
            session_token=access_token,
            user=UserResponse(
                id=user_id,
                username=username,
                email="",  # Will be filled by the service
                created_at=datetime.utcnow(),
                is_active=True,
                storage_provider="local"
            ),
            expires_at=expires_at
        )

    async def validate_session(self, token: str) -> Optional[dict]:
        """Validate a session token"""
        if token not in self.active_sessions:
            return None
        
        session = self.active_sessions[token]
        if session["expires_at"] < datetime.utcnow():
            del self.active_sessions[token]
            return None
        
        return session

    async def invalidate_session(self, token: str) -> bool:
        """Invalidate a session token"""
        if token in self.active_sessions:
            del self.active_sessions[token]
            return True
        return False

    async def refresh_session(self, refresh_token: str) -> Optional[UserSession]:
        """Refresh a session using refresh token"""
        try:
            payload = AuthUtils.verify_token(refresh_token)
            if payload.get("type") != "refresh":
                return None
            
            user_id = UUID(payload.get("user_id"))
            username = payload.get("username")
            
            # Create new session
            return await self.create_session(user_id, username)
            
        except Exception:
            return None

# Global session manager
session_manager = SessionManager()

class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed"""
        now = datetime.utcnow()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if (now - req_time).total_seconds() < self.window_seconds
        ]
        
        # Check if under limit
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(now)
            return True
        
        return False

    def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key"""
        now = datetime.utcnow()
        
        if key not in self.requests:
            return self.max_requests
        
        # Remove old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if (now - req_time).total_seconds() < self.window_seconds
        ]
        
        return max(0, self.max_requests - len(self.requests[key]))

# Global rate limiter
rate_limiter = RateLimiter()

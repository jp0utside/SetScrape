# Shared utilities and models for the music player system

from .database_models import (
    Base, User, CacheEntry, Download, UserSession
)

from .models import (
    # Base models
    BaseResponse, PaginatedResponse,
    
    # User models
    UserCreate, UserLogin, UserResponse, UserSession,
    
    # Internet Archive models (real-time)
    ArchiveItem, ArchiveTrack, ArchiveSearchResponse,
    
    # Cache models
    CacheEntryResponse,
    
    # Download models
    DownloadCreate, DownloadResponse, DownloadProgress,
    
    # WebSocket models
    WebSocketMessage, DownloadProgressMessage,
    
    # Response models
    ErrorResponse, APIResponse, HealthCheckResponse, StatsResponse
)

from .database import (
    get_db, init_db, close_db, AsyncSessionLocal,
    check_db_health, DatabaseUtils
)

from .auth import (
    AuthUtils, AuthDependencies, RateLimiter, SessionManager
)

__all__ = [
    # Database models
    "Base", "User", "CacheEntry", "Download", "UserSession",
    
    # Pydantic models
    "BaseResponse", "PaginatedResponse", "UserCreate", "UserLogin", "UserResponse", "UserSession",
    "ArchiveItem", "ArchiveTrack", "ArchiveSearchResponse", "CacheEntryResponse",
    "DownloadCreate", "DownloadResponse", "DownloadProgress",
    "WebSocketMessage", "DownloadProgressMessage", "ErrorResponse", "APIResponse", "HealthCheckResponse", "StatsResponse",
    
    # Database utilities
    "get_db", "init_db", "close_db", "AsyncSessionLocal", "check_db_health", "DatabaseUtils",
    
    # Authentication utilities
    "AuthUtils", "AuthDependencies", "RateLimiter", "SessionManager"
]

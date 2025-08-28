from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

# Enums
class DownloadStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"

class StorageProvider(str, Enum):
    LOCAL = "local"
    S3 = "s3"
    GOOGLE_CLOUD = "google_cloud"

# Base Models
class BaseResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None

class PaginatedResponse(BaseResponse):
    total: int = Field(ge=0)
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    total_pages: int = Field(ge=0)

# User Models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = Field(None, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: Optional[str] = None
    created_at: datetime
    is_active: bool
    storage_provider: str

class UserSession(BaseModel):
    session_token: str
    user: UserResponse
    expires_at: Optional[datetime] = None

# Internet Archive Models (Real-time)
class ArchiveTrack(BaseModel):
    track_number: Optional[int] = None
    title: str
    filename: str
    file_format: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[int] = None
    download_url: Optional[str] = None

class ArchiveItem(BaseModel):
    identifier: str
    title: str
    artist: Optional[str] = None
    date: Optional[datetime] = None
    venue: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    taper: Optional[str] = None
    lineage: Optional[str] = None
    total_tracks: int = Field(default=0, ge=0)
    total_size: int = Field(default=0, ge=0)
    tracks: Optional[List[ArchiveTrack]] = None
    # Engagement statistics
    downloads: int = Field(default=0, ge=0)

class ArchiveSearchResponse(PaginatedResponse):
    results: List[ArchiveItem]

# Cache Models
class CacheEntryResponse(BaseModel):
    id: UUID
    cache_key: str
    cache_type: str
    expires_at: datetime
    created_at: datetime
    last_accessed: datetime
    access_count: int

# Aggregated Concert Models
class ConcertRecordingResponse(BaseModel):
    id: UUID
    archive_identifier: str
    title: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    taper: Optional[str] = None
    lineage: Optional[str] = None
    total_tracks: int = Field(default=0, ge=0)
    total_size: int = Field(default=0, ge=0)
    tracks: Optional[List[ArchiveTrack]] = None
    created_at: datetime

class AggregatedConcertResponse(BaseModel):
    id: UUID
    concert_key: str
    artist: str
    date: datetime
    venue: Optional[str] = None
    location: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    taper: Optional[str] = None
    lineage: Optional[str] = None
    total_recordings: int = Field(default=0, ge=0)
    total_tracks: int = Field(default=0, ge=0)
    total_size: int = Field(default=0, ge=0)
    recordings: List[ConcertRecordingResponse]
    indexed_at: datetime
    last_updated: datetime

class ConcertSearchResponse(PaginatedResponse):
    results: List[AggregatedConcertResponse]

# Download Models
class DownloadCreate(BaseModel):
    archive_identifier: str
    filename: str
    track_title: Optional[str] = None

class DownloadResponse(BaseModel):
    id: UUID
    user_id: UUID
    archive_identifier: str
    filename: str
    track_title: Optional[str] = None
    status: DownloadStatus
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_url: Optional[str] = None
    started_at: Optional[datetime] = None
    download_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

class DownloadProgress(BaseModel):
    download_id: UUID
    progress: float = Field(ge=0.0, le=100.0)
    status: DownloadStatus
    message: Optional[str] = None

# WebSocket Models
class WebSocketMessage(BaseModel):
    type: str = Field(..., min_length=1)
    data: Dict[str, Any]

class DownloadProgressMessage(WebSocketMessage):
    type: str = Field(default="download_progress", pattern=r"^download_progress$")
    data: DownloadProgress

# Response Models
class ErrorResponse(BaseModel):
    detail: str

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class HealthCheckResponse(BaseModel):
    status: str = Field(..., pattern=r"^(healthy|unhealthy|degraded)$")
    service: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")

class StatsResponse(BaseModel):
    total_users: int = Field(ge=0)
    total_downloads: int = Field(ge=0)
    total_concerts: int = Field(ge=0)
    total_recordings: int = Field(ge=0)
    cache_stats: Dict[str, Any]
    download_stats: Dict[str, Any]

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Float, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    storage_provider = Column(String(50), default='local')
    storage_config = Column(Text)

class CacheEntry(Base):
    __tablename__ = "cache_entries"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cache_key = Column(String(500), unique=True, nullable=False)
    cache_data = Column(Text, nullable=False)  # JSON data
    cache_type = Column(String(50), nullable=False)  # 'search', 'metadata', 'item'
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    last_accessed = Column(DateTime, server_default=func.now(), onupdate=func.now())
    access_count = Column(Integer, default=0)

class Download(Base):
    __tablename__ = "downloads"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    archive_identifier = Column(String(255), nullable=False)  # Internet Archive identifier
    filename = Column(String(255), nullable=False)
    track_title = Column(String(500))
    status = Column(String(20), default='pending')  # 'pending', 'downloading', 'completed', 'failed'
    progress = Column(Float, default=0.0)
    file_path = Column(String(500))
    file_size = Column(Integer)
    download_url = Column(Text)
    started_at = Column(DateTime)
    download_completed_at = Column(DateTime)
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class AggregatedConcert(Base):
    __tablename__ = "aggregated_concerts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    concert_key = Column(String(500), unique=True, nullable=False)  # artist|date|venue
    artist = Column(String(255), nullable=False)
    date = Column(DateTime, nullable=False)
    venue = Column(String(255))
    location = Column(String(255))
    title = Column(String(500))
    description = Column(Text)
    source = Column(String(255))
    taper = Column(String(255))
    lineage = Column(String(255))
    total_recordings = Column(Integer, default=0)
    total_tracks = Column(Integer, default=0)
    total_size = Column(Integer, default=0)
    indexed_at = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

class ConcertRecording(Base):
    __tablename__ = "concert_recordings"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    concert_id = Column(String, ForeignKey('aggregated_concerts.id'), nullable=False)
    archive_identifier = Column(String(255), nullable=False)
    title = Column(String(500))
    description = Column(Text)
    source = Column(String(255))
    taper = Column(String(255))
    lineage = Column(String(255))
    total_tracks = Column(Integer, default=0)
    total_size = Column(Integer, default=0)
    tracks = Column(Text)  # JSON array of track info
    created_at = Column(DateTime, server_default=func.now())

# Define relationships
User.sessions = relationship("UserSession", back_populates="user")
User.downloads = relationship("Download", back_populates="user")

UserSession.user = relationship("User", back_populates="sessions")
Download.user = relationship("User", back_populates="downloads")

AggregatedConcert.recordings = relationship("ConcertRecording", back_populates="concert", cascade="all, delete-orphan")
ConcertRecording.concert = relationship("AggregatedConcert", back_populates="recordings")

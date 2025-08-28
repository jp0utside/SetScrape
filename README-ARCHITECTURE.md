# 🏗️ Music Player System - Architecture Documentation

## 📋 Overview

This document describes the **4-service microservices architecture** for the Music Player System, designed for local storage and offline-first functionality with Internet Archive integration.

## 🎯 Architecture Goals

- **Real-time Access**: Direct Internet Archive API calls with smart caching
- **Local Storage**: Music files stored locally for offline playback
- **Scalable**: Microservices architecture for easy scaling
- **Offline-First**: Works without internet connection once music is downloaded
- **Internet Archive Integration**: Leverages vast music collection

## 🏢 Service Architecture

### 🎵 Main API Service (Port 8000)
**Purpose**: API Gateway and user management

**Responsibilities**:
- User authentication and session management
- Service coordination and routing
- Web interface serving
- API documentation

**Key Endpoints**:
- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication
- `GET /music/search` - Search music (routes to Browse Service)
- `POST /downloads` - Start downloads (routes to Download Service)
- `GET /concerts` - Get aggregated concerts (routes to Aggregation Service)

### 🔍 Aggregation Service (Port 8003)
**Purpose**: Intelligent concert aggregation and grouping

**Responsibilities**:
- Groups recordings by concert instances (artist + date)
- Provides concert-level views of multiple recordings
- Smart caching of aggregation results
- Concert metadata enrichment

**Key Endpoints**:
- `GET /concerts` - Get aggregated concerts
- `GET /concerts/{concert_id}` - Get specific concert details
- `GET /concerts/recent` - Get recent concerts
- `GET /concerts/search` - Search concerts

### ⬇️ Download Service (Port 8002)
**Purpose**: Download management and file processing

**Responsibilities**:
- Download music files from Internet Archive
- Track download progress and status
- File validation and storage
- Real-time progress via WebSockets
- Download history management

**Key Endpoints**:
- `POST /downloads` - Start a download
- `GET /downloads` - Get user's downloads
- `GET /downloads/{download_id}` - Get specific download
- `DELETE /downloads/{download_id}` - Cancel download
- `WS /ws/downloads/{user_id}` - Real-time progress

### 🌐 Browse Service (Port 8001)
**Purpose**: Real-time Internet Archive API integration and caching

**Responsibilities**:
- Direct API calls to Internet Archive etree collection
- Smart caching of search results and metadata
- Directory browsing of archive items
- File listing and metadata extraction
- Performance optimization through intelligent caching

**Key Endpoints**:
- `GET /browse/search` - Search Internet Archive
- `GET /browse/items/{identifier}` - Get item details
- `GET /browse/directory/{identifier}` - Browse item directory
- `GET /browse/cache/stats` - Cache statistics
- `POST /browse/cache/clear` - Clear cache

## 🗄️ Data Storage Architecture

### Database Schema (SQLite)

#### Core Tables

**`users`** - User accounts and authentication
- `id` (UUID) - Primary key
- `username` (String) - Unique username
- `email` (String) - Unique email
- `password_hash` (String) - Bcrypt hashed password
- `created_at` (DateTime) - Account creation time
- `is_active` (Boolean) - Account status
- `storage_provider` (String) - Storage configuration

**`downloads`** - Download history and status
- `id` (UUID) - Primary key
- `user_id` (UUID) - Foreign key to users
- `archive_identifier` (String) - Internet Archive identifier
- `filename` (String) - File being downloaded
- `status` (String) - Download status (pending, downloading, completed, failed)
- `progress` (Float) - Download progress percentage
- `file_path` (String) - Local file path
- `file_size` (Integer) - Downloaded file size
- `download_url` (Text) - Original download URL
- `started_at` (DateTime) - When download started
- `download_completed_at` (DateTime) - When download completed
- `error_message` (Text) - Error details if failed



**`user_sessions`** - User authentication sessions
- `id` (UUID) - Primary key
- `user_id` (UUID) - Foreign key to users
- `session_token` (String) - JWT session token
- `expires_at` (DateTime) - Session expiration
- `created_at` (DateTime) - Session creation time

**`search_history`** - User search history
- `id` (UUID) - Primary key
- `user_id` (UUID) - Foreign key to users
- `query` (String) - Search query
- `search_type` (String) - Type of search
- `results_count` (Integer) - Number of results
- `created_at` (DateTime) - Search time

**`cache_entries`** - Browse service cache
- `id` (UUID) - Primary key
- `cache_key` (String) - Cache key
- `cache_data` (Text) - Cached data (JSON)
- `cache_type` (String) - Type of cached data
- `expires_at` (DateTime) - Cache expiration
- `created_at` (DateTime) - Cache creation time

**`aggregated_concerts`** - Concert aggregation data
- `id` (UUID) - Primary key
- `artist` (String) - Artist name
- `date` (DateTime) - Concert date
- `venue` (String) - Venue name
- `location` (String) - Location
- `recordings_count` (Integer) - Number of recordings
- `total_tracks` (Integer) - Total tracks across recordings
- `metadata` (Text) - Concert metadata (JSON)
- `created_at` (DateTime) - When aggregated
- `updated_at` (DateTime) - Last update

**`concert_recordings`** - Recordings within concerts
- `id` (UUID) - Primary key
- `concert_id` (UUID) - Foreign key to aggregated_concerts
- `archive_identifier` (String) - Internet Archive identifier
- `title` (String) - Recording title
- `source` (String) - Recording source
- `taper` (String) - Person who recorded
- `lineage` (Text) - Recording lineage
- `total_tracks` (Integer) - Number of tracks
- `total_size` (Integer) - Total size in bytes
- `metadata` (Text) - Recording metadata (JSON)

### Relationships

```
users (1) ←→ (many) downloads
users (1) ←→ (many) user_sessions
users (1) ←→ (many) search_history

aggregated_concerts (1) ←→ (many) concert_recordings
```

## 🔄 Data Flow

### 1. Music Discovery Flow
```
Internet Archive → Browse Service → Cache → Main API → User
```

1. **Browse Service** queries Internet Archive etree collection in real-time
2. **Search results** are cached for performance
3. **Main API** coordinates browse requests and returns results
4. **User** receives search results with metadata

### 2. Concert Aggregation Flow
```
Browse Service → Aggregation Service → Main API → User
```

1. **Browse Service** provides raw archive items
2. **Aggregation Service** groups items by artist + date
3. **Concert instances** are created with metadata
4. **Main API** serves aggregated concerts to user

### 3. Download Flow
```
User Request → Main API → Download Service → Internet Archive → Local Storage
```

1. **User** requests download via Main API
2. **Main API** forwards request to Download Service
3. **Download Service** downloads file from Internet Archive
4. **File** is stored in user's local directory
5. **Progress** is tracked and reported via WebSocket



## 🛠️ Technology Stack

### Backend Services
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM
- **SQLite** - Lightweight, serverless database
- **Pydantic** - Data validation using Python type annotations
- **JWT** - JSON Web Tokens for authentication
- **Bcrypt** - Password hashing
- **HTTPX** - Async HTTP client for service communication
- **AIOFiles** - Async file I/O operations

### Development & Deployment
- **Uvicorn** - ASGI server for running FastAPI
- **Python 3.12** - Modern Python with async/await support
- **Virtual Environment** - Isolated Python environment
- **Local Development** - No external dependencies required

### Internet Archive Integration
- **Internet Archive API** - Advanced search and metadata
- **Etree Collection** - Live music recordings
- **Metadata API** - Detailed file information
- **Direct Downloads** - File download URLs

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./data/music_player.db

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Service URLs
BROWSE_SERVICE_URL=http://127.0.0.1:8001
DOWNLOAD_SERVICE_URL=http://127.0.0.1:8002
AGGREGATION_SERVICE_URL=http://127.0.0.1:8003

# Development
DEBUG=true
LOG_LEVEL=INFO
```

### File Structure
```
├── backend/
│   ├── main_api_service/     # Main API Service (Port 8000)
│   ├── aggregation_service/  # Aggregation Service (Port 8003)
│   ├── download_service/     # Download Service (Port 8002)
│   └── browse_service/       # Browse Service (Port 8001)
├── shared/                   # Shared utilities and models
├── data/                    # SQLite database
├── downloads/               # Downloaded music files
├── start.py                 # Service startup script
└── requirements.txt         # Python dependencies
```

## 🚀 Scalability Considerations

### Current Architecture
- **Single Database**: SQLite for simplicity
- **In-Memory Tasks**: Background tasks in memory
- **Local Storage**: Files stored locally
- **Service Communication**: HTTP between services

### Future Scalability
- **Database**: PostgreSQL for production
- **Caching**: Redis for session and cache management
- **File Storage**: Cloud storage (S3, Google Cloud)
- **Load Balancing**: Multiple service instances
- **Containerization**: Docker and Kubernetes
- **Message Queues**: Celery/RabbitMQ for background tasks

## 🔒 Security Considerations

### Authentication
- **JWT Tokens**: Stateless authentication
- **Password Hashing**: Bcrypt for secure password storage
- **Session Management**: Database-backed sessions
- **Rate Limiting**: Request rate limiting per user

### Data Protection
- **Input Validation**: Pydantic models for data validation
- **SQL Injection Prevention**: SQLAlchemy ORM
- **File Validation**: Audio file type checking
- **User Isolation**: User-specific data access

### API Security
- **CORS Configuration**: Cross-origin resource sharing
- **Error Handling**: Secure error messages
- **Logging**: Comprehensive request logging
- **Health Checks**: Service health monitoring

## 📊 Monitoring & Observability

### Health Checks
- **Service Health**: `/health` endpoints for all services
- **Database Health**: Connection and query monitoring
- **Service Communication**: Inter-service health checks

### Metrics & Statistics
- **User Statistics**: User counts and activity
- **Download Statistics**: Download counts and sizes
- **Search Statistics**: Search queries and results
- **System Statistics**: Service performance metrics

### Logging
- **Request Logging**: All API requests logged
- **Error Logging**: Comprehensive error tracking
- **Performance Logging**: Response time monitoring
- **Background Job Logging**: Task execution tracking

## 🔮 Future Enhancements

### Planned Features
- **Mobile Application**: React Native mobile app
- **Cloud Storage**: Integration with cloud providers
- **Advanced Search**: Elasticsearch for better search
- **Audio Processing**: Audio analysis and metadata extraction
- **Social Features**: User sharing and recommendations
- **Library Management**: User library and playlist functionality

### Technical Improvements
- **Microservices**: Full containerization
- **API Gateway**: Centralized API management
- **Event Sourcing**: Event-driven architecture
- **CQRS**: Command Query Responsibility Segregation
- **GraphQL**: Alternative to REST API

This architecture provides a solid foundation for a scalable, offline-first music player system with rich Internet Archive integration.

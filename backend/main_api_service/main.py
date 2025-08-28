import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, timedelta
import httpx

from shared.database import get_db, init_db, close_db
from shared.models import (
    UserCreate, UserLogin, UserResponse, UserSession,
    ArchiveItem, ArchiveSearchResponse,
    DownloadCreate, DownloadResponse,
    HealthCheckResponse, StatsResponse
)
from shared.database_models import User, Download, AggregatedConcert, ConcertRecording
from shared.auth import AuthDependencies, AuthUtils
from backend.main_api_service.services import UserService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service URLs
BROWSE_SERVICE_URL = os.getenv("BROWSE_SERVICE_URL", "http://127.0.0.1:8001")
DOWNLOAD_SERVICE_URL = os.getenv("DOWNLOAD_SERVICE_URL", "http://127.0.0.1:8002")
AGGREGATION_SERVICE_URL = os.getenv("AGGREGATION_SERVICE_URL", "http://127.0.0.1:8003")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Main API Service...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down Main API Service...")
    await close_db()
    
    # Ensure all httpx connections are closed
    import asyncio
    try:
        # Cancel any pending tasks
        tasks = [task for task in asyncio.all_tasks() if not task.done()]
        for task in tasks:
            task.cancel()
        
        # Wait for tasks to be cancelled
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Create FastAPI app
app = FastAPI(
    title="Music Player Main API",
    description="Main API service for music player system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="backend/main_api_service/static"), name="static")

@app.get("/")
async def read_root():
    """Serve the web interface"""
    return FileResponse("backend/main_api_service/static/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(
        status="healthy",
        service="main-api-service",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )

@app.get("/stats")
async def get_stats(
    current_user: dict = Depends(AuthDependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get system statistics"""
    try:
        # Get user stats
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar()
        
        # Get download stats
        total_downloads_result = await db.execute(select(func.count(Download.id)))
        total_downloads = total_downloads_result.scalar()
        
        # Get concert stats
        total_concerts_result = await db.execute(select(func.count(AggregatedConcert.id)))
        total_concerts = total_concerts_result.scalar()
        
        # Get recording stats
        total_recordings_result = await db.execute(select(func.count(ConcertRecording.id)))
        total_recordings = total_recordings_result.scalar()
        
        # Get service stats
        service_stats = {}
        services = [
            ("download", f"{DOWNLOAD_SERVICE_URL}/stats"),
            ("browse", f"{BROWSE_SERVICE_URL}/stats")
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for service_name, url in services:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        service_stats[service_name] = response.json()
                    else:
                        service_stats[service_name] = {"status": "unavailable"}
                except Exception as e:
                    service_stats[service_name] = {"status": "error", "error": str(e)}
        
        return StatsResponse(
            total_users=total_users,
            total_downloads=total_downloads,
            total_concerts=total_concerts,
            total_recordings=total_recordings,
            cache_stats=service_stats.get("browse", {}),
            download_stats=service_stats.get("download", {})
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")

# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    try:
        user = await UserService.create_user(db, user_data)
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            is_active=user.is_active,
            storage_provider=user.storage_provider
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail="Failed to register user")

@app.post("/auth/login", response_model=UserSession)
async def login_user(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login user and create session"""
    try:
        user = await UserService.authenticate_user(db, login_data.username, login_data.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create session
        session_token = AuthUtils.create_access_token(
            data={"user_id": str(user.id), "username": user.username}
        )
        
        # Create session using session manager
        session = await UserService.create_user_session(db, str(user.id), user.username)
        
        return UserSession(
            session_token=session.session_token,
            user=session.user,
            expires_at=session.expires_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in user: {e}")
        raise HTTPException(status_code=500, detail="Failed to login user")

@app.post("/auth/logout")
async def logout_user(
    current_user: dict = Depends(AuthDependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout user and invalidate session"""
    try:
        await UserService.invalidate_user_session(db, current_user["user_id"])
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Error logging out user: {e}")
        raise HTTPException(status_code=500, detail="Failed to logout user")

# Music browse endpoints
@app.get("/music/browse")
async def browse_music(
    query: Optional[str] = Query(None, description="Search query"),
    date_range: Optional[str] = Query(None, description="Date range (e.g., '30d', '90d', '1y')"),
    artist: Optional[str] = Query(None, description="Filter by artist"),
    venue: Optional[str] = Query(None, description="Filter by venue"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Browse Internet Archive live music using the Browse Service"""
    try:
        # Call browse service
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "query": query,
                "date_range": date_range,
                "artist": artist,
                "venue": venue,
                "page": page,
                "per_page": per_page
            }
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            response = await client.get(f"{BROWSE_SERVICE_URL}/browse", params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Browse service error: {e}")
        raise HTTPException(status_code=502, detail="Browse service unavailable")
    except Exception as e:
        logger.error(f"Error browsing music: {e}")
        raise HTTPException(status_code=500, detail="Failed to browse music")

@app.get("/music/item/{identifier}")
async def get_item_details(
    identifier: str,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific Internet Archive item"""
    try:
        # Call browse service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{BROWSE_SERVICE_URL}/item/{identifier}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Browse service error: {e}")
        raise HTTPException(status_code=502, detail="Browse service unavailable")
    except Exception as e:
        logger.error(f"Error getting item details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get item details")

@app.get("/music/directory/{identifier}")
async def get_directory_structure(
    identifier: str,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Get directory structure and available files for an archive identifier"""
    try:
        # Call browse service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{BROWSE_SERVICE_URL}/directory/{identifier}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Browse service error: {e}")
        raise HTTPException(status_code=502, detail="Browse service unavailable")
    except Exception as e:
        logger.error(f"Error getting directory structure: {e}")
        raise HTTPException(status_code=500, detail="Failed to get directory structure")

# Concert aggregation endpoints


@app.get("/concerts")
async def browse_concerts(
    query: Optional[str] = Query(None, description="Search query"),
    date_range: Optional[str] = Query(None, description="Date range (e.g., '30d', '90d')"),
    artist: Optional[str] = Query(None, description="Filter by artist"),
    venue: Optional[str] = Query(None, description="Filter by venue"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Concerts per page"),
    sort_by: Optional[str] = Query("date", description="Sort by field (date, artist, venue)"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc, desc)"),
    filter_by_concert_date: Optional[bool] = Query(False, description="Filter by concert date instead of upload date"),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Browse concerts from local database using the Aggregation Service"""
    try:
        # Call aggregation service
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "query": query,
                "date_range": date_range,
                "artist": artist,
                "venue": venue,
                "page": page,
                "per_page": per_page,
                "sort_by": sort_by,
                "sort_order": sort_order,
                "filter_by_concert_date": filter_by_concert_date
            }
            params = {k: v for k, v in params.items() if v is not None}
            
            response = await client.get(f"{AGGREGATION_SERVICE_URL}/concerts", params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Aggregation service error: {e}")
        raise HTTPException(status_code=502, detail="Aggregation service unavailable")
    except Exception as e:
        logger.error(f"Error browsing concerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to browse concerts")

@app.get("/concerts/{concert_key}")
async def get_concert_details(
    concert_key: str,
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific concert"""
    try:
        # Call aggregation service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{AGGREGATION_SERVICE_URL}/concerts/{concert_key}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Aggregation service error: {e}")
        raise HTTPException(status_code=502, detail="Aggregation service unavailable")
    except Exception as e:
        logger.error(f"Error getting concert details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get concert details")

# Download endpoints
@app.post("/downloads", response_model=DownloadResponse)
async def start_download(
    download_data: DownloadCreate,
    current_user: dict = Depends(AuthDependencies.get_current_user),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Start a download using the Download Service"""
    try:
        # Get the original Authorization header
        auth_header = request.headers.get("Authorization", "")
        
        # Call download service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{DOWNLOAD_SERVICE_URL}/downloads",
                json=download_data.dict(),
                headers={"Authorization": auth_header}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Download service error: {e}")
        raise HTTPException(status_code=502, detail="Download service unavailable")
    except Exception as e:
        logger.error(f"Error starting download: {e}")
        raise HTTPException(status_code=500, detail="Failed to start download")

@app.get("/downloads", response_model=List[DownloadResponse])
async def get_downloads(
    current_user: dict = Depends(AuthDependencies.get_current_user),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Get user downloads using the Download Service"""
    try:
        # Get the original Authorization header
        auth_header = request.headers.get("Authorization", "")
        
        # Call download service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{DOWNLOAD_SERVICE_URL}/downloads",
                headers={"Authorization": auth_header}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Download service error: {e}")
        raise HTTPException(status_code=502, detail="Download service unavailable")
    except Exception as e:
        logger.error(f"Error getting downloads: {e}")
        raise HTTPException(status_code=500, detail="Failed to get downloads")

@app.get("/downloads/{download_id}", response_model=DownloadResponse)
async def get_download(
    download_id: str,
    current_user: dict = Depends(AuthDependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific download using the Download Service"""
    try:
        # Call download service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{DOWNLOAD_SERVICE_URL}/downloads/{download_id}",
                headers={"Authorization": f"Bearer {current_user.get('token', '')}"}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Download service error: {e}")
        raise HTTPException(status_code=502, detail="Download service unavailable")
    except Exception as e:
        logger.error(f"Error getting download: {e}")
        raise HTTPException(status_code=500, detail="Failed to get download")

@app.delete("/downloads/{download_id}")
async def cancel_download(
    download_id: str,
    current_user: dict = Depends(AuthDependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a download using the Download Service"""
    try:
        # Call download service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{DOWNLOAD_SERVICE_URL}/downloads/{download_id}",
                headers={"Authorization": f"Bearer {current_user.get('token', '')}"}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Download service error: {e}")
        raise HTTPException(status_code=502, detail="Download service unavailable")
    except Exception as e:
        logger.error(f"Error cancelling download: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel download")

@app.get("/downloads/{download_id}/file")
async def download_file(
    download_id: str,
    current_user: dict = Depends(AuthDependencies.get_current_user),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """Download/save a completed file to the user's system"""
    try:
        # Get the original Authorization header
        auth_header = request.headers.get("Authorization", "")
        
        # Get the download info first to verify it exists and is completed
        async with httpx.AsyncClient(timeout=30.0) as client:
            download_response = await client.get(
                f"{DOWNLOAD_SERVICE_URL}/downloads/{download_id}",
                headers={"Authorization": auth_header}
            )
            download_response.raise_for_status()
            download_data = download_response.json()
            
            if download_data.get("status") != "completed":
                raise HTTPException(status_code=400, detail="Download not completed yet")
            
            # Now get the actual file
            file_response = await client.get(
                f"{DOWNLOAD_SERVICE_URL}/downloads/{download_id}/file",
                headers={"Authorization": auth_header}
            )
            file_response.raise_for_status()
            
            # Return file response with proper headers
            from fastapi.responses import Response
            return Response(
                content=file_response.content,
                media_type=file_response.headers.get("content-type", "application/octet-stream"),
                headers={
                    "Content-Disposition": f"attachment; filename=\"{download_data.get('filename', 'download')}\"",
                    "Content-Length": str(len(file_response.content))
                }
            )
    except httpx.HTTPStatusError as e:
        logger.error(f"Download service error: {e}")
        raise HTTPException(status_code=502, detail="Download service unavailable")
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail="Failed to download file")

# Library and playlist endpoints removed - focusing on browsing and downloading only

# Cache management endpoints
@app.get("/admin/cache")
async def get_cache_info(
    current_user: dict = Depends(AuthDependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get cache information using the Browse Service"""
    try:
        # Call browse service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{BROWSE_SERVICE_URL}/cache")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Browse service error: {e}")
        raise HTTPException(status_code=502, detail="Browse service unavailable")
    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache info")

@app.delete("/admin/cache")
async def clear_cache(
    cache_type: Optional[str] = Query(None, description="Clear specific cache type"),
    current_user: dict = Depends(AuthDependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clear cache using the Browse Service"""
    try:
        # Call browse service
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {"cache_type": cache_type} if cache_type else {}
            response = await client.delete(f"{BROWSE_SERVICE_URL}/cache", params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Browse service error: {e}")
        raise HTTPException(status_code=502, detail="Browse service unavailable")
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return {"detail": "Internal server error"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

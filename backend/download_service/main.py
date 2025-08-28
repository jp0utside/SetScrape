import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime
import httpx
import aiofiles
from pathlib import Path

from shared.database import get_db, init_db, close_db, AsyncSessionLocal
from shared.models import (
    DownloadCreate, DownloadResponse, DownloadProgress,
    HealthCheckResponse, StatsResponse
)
from pydantic import BaseModel
from typing import Dict, Any
from shared.database_models import Download, User
from shared.auth import AuthDependencies

# New models for directory browsing
class ArchiveFile(BaseModel):
    filename: str
    size: Optional[int] = None
    last_modified: Optional[str] = None
    file_type: str  # 'audio', 'image', 'metadata', 'other'
    format: Optional[str] = None  # 'flac', 'mp3', 'png', etc.

class ArchiveDirectory(BaseModel):
    identifier: str
    files: List[ArchiveFile]
    total_files: int
    total_size: int
    audio_files: List[ArchiveFile]
    image_files: List[ArchiveFile]
    metadata_files: List[ArchiveFile]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download configuration
DOWNLOAD_DIR = Path("./downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Download Service...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down Download Service...")
    await close_db()

# Create FastAPI app
app = FastAPI(
    title="Music Download Service",
    description="Service for downloading music files from Internet Archive",
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(
        status="healthy",
        service="download-service",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )

@app.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get download service statistics"""
    try:
        # Get total downloads count
        total_downloads_result = await db.execute(select(func.count(Download.id)))
        total_downloads = total_downloads_result.scalar()
        
        # Get completed downloads count
        completed_downloads_result = await db.execute(
            select(func.count(Download.id))
            .where(Download.status == "completed")
        )
        completed_downloads = completed_downloads_result.scalar()
        
        # Get failed downloads count
        failed_downloads_result = await db.execute(
            select(func.count(Download.id))
            .where(Download.status == "failed")
        )
        failed_downloads = failed_downloads_result.scalar()
        
        # Get total downloaded size
        total_size_result = await db.execute(
            select(func.sum(Download.file_size))
            .where(Download.status == "completed")
        )
        total_size = total_size_result.scalar() or 0
        
        return StatsResponse(
            total_users=0,  # Not tracked in download service
            total_downloads=total_downloads,
            total_concerts=0,  # Not tracked in download service
            total_recordings=0,  # Not tracked in download service
            cache_stats={"total_size_bytes": total_size},
            download_stats={
                "total_downloads": total_downloads,
                "completed_downloads": completed_downloads,
                "failed_downloads": failed_downloads,
                "total_size_bytes": total_size
            }
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")

@app.post("/test-download")
async def test_download(
    download_request: DownloadCreate,
    db: AsyncSession = Depends(get_db)
):
    """Test download endpoint without authentication"""
    try:
        # Create download record with a test user ID
        download = Download(
            user_id="00000000-0000-0000-0000-000000000000",
            archive_identifier=download_request.archive_identifier,
            filename=download_request.filename,
            track_title=download_request.track_title,
            status="pending",
            progress=0.0,
            download_url=f"https://archive.org/download/{download_request.archive_identifier}/{download_request.filename}",
            created_at=datetime.utcnow()
        )
        
        db.add(download)
        await db.commit()
        await db.refresh(download)
        
        return DownloadResponse(
            id=download.id,
            user_id=download.user_id,
            archive_identifier=download.archive_identifier,
            filename=download.filename,
            track_title=download.track_title,
            status=download.status,
            progress=download.progress,
            file_path=download.file_path,
            file_size=download.file_size,
            download_url=download.download_url,
            started_at=download.started_at,
            download_completed_at=download.download_completed_at,
            error_message=download.error_message,
            created_at=download.created_at
        )
        
    except Exception as e:
        logger.error(f"Error in test download: {e}")
        raise HTTPException(status_code=500, detail=f"Test download failed: {str(e)}")

@app.post("/downloads", response_model=DownloadResponse)
async def start_download(
    download_request: DownloadCreate,
    current_user: dict = Depends(AuthDependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a download for a specific file from an archive"""
    try:
        logger.info(f"Starting download for user: {current_user['user_id']}")
        logger.info(f"Download request: {download_request}")
        
        # Check if download already exists for this user, archive, and filename
        existing_download_result = await db.execute(
            select(Download).where(
                Download.user_id == current_user["user_id"],
                Download.archive_identifier == download_request.archive_identifier,
                Download.filename == download_request.filename
            )
        )
        existing_download = existing_download_result.scalar_one_or_none()
        
        if existing_download:
            if existing_download.status == "completed":
                return DownloadResponse(
                    id=existing_download.id,
                    user_id=existing_download.user_id,
                    archive_identifier=existing_download.archive_identifier,
                    filename=existing_download.filename,
                    track_title=existing_download.track_title,
                    status=existing_download.status,
                    progress=existing_download.progress,
                    file_path=existing_download.file_path,
                    file_size=existing_download.file_size,
                    download_url=existing_download.download_url,
                    started_at=existing_download.started_at,
                    download_completed_at=existing_download.download_completed_at,
                    error_message=existing_download.error_message,
                    created_at=existing_download.created_at
                )
            else:
                raise HTTPException(status_code=400, detail="Download already in progress")
        
        # Create download URL
        download_url = f"https://archive.org/download/{download_request.archive_identifier}/{download_request.filename}"
        
        # Create download record
        download = Download(
            user_id=current_user["user_id"],
            archive_identifier=download_request.archive_identifier,
            filename=download_request.filename,
            track_title=download_request.track_title,
            status="pending",
            progress=0.0,
            download_url=download_url,
            created_at=datetime.utcnow()
        )
        
        db.add(download)
        await db.commit()
        await db.refresh(download)
        
        # Start background download
        asyncio.create_task(process_download(download.id))
        
        return DownloadResponse(
            id=download.id,
            user_id=download.user_id,
            archive_identifier=download.archive_identifier,
            filename=download.filename,
            track_title=download.track_title,
            status=download.status,
            progress=download.progress,
            file_path=download.file_path,
            file_size=download.file_size,
            download_url=download.download_url,
            started_at=download.started_at,
            download_completed_at=download.download_completed_at,
            error_message=download.error_message,
            created_at=download.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting download: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to start download: {str(e)}")

@app.get("/downloads", response_model=List[DownloadResponse])
async def get_user_downloads(
    current_user: dict = Depends(AuthDependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all downloads for the current user"""
    try:
        downloads_result = await db.execute(
            select(Download)
            .where(Download.user_id == current_user["user_id"])
            .order_by(Download.created_at.desc())
        )
        downloads = downloads_result.scalars().all()
        
        download_responses = []
        for download in downloads:
            download_responses.append(DownloadResponse(
                id=download.id,
                user_id=download.user_id,
                archive_identifier=download.archive_identifier,
                filename=download.filename,
                track_title=download.track_title,
                status=download.status,
                progress=download.progress,
                file_path=download.file_path,
                file_size=download.file_size,
                download_url=download.download_url,
                started_at=download.started_at,
                download_completed_at=download.download_completed_at,
                error_message=download.error_message,
                created_at=download.created_at
            ))
        
        return download_responses
        
    except Exception as e:
        logger.error(f"Error getting downloads: {e}")
        raise HTTPException(status_code=500, detail="Failed to get downloads")

@app.get("/downloads/{download_id}", response_model=DownloadResponse)
async def get_download(
    download_id: str,
    current_user: dict = Depends(AuthDependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific download by ID"""
    try:
        download_result = await db.execute(
            select(Download).where(
                Download.id == download_id,
                Download.user_id == current_user["user_id"]
            )
        )
        download = download_result.scalar_one_or_none()
        
        if not download:
            raise HTTPException(status_code=404, detail="Download not found")
        
        return DownloadResponse(
            id=download.id,
            user_id=download.user_id,
            archive_identifier=download.archive_identifier,
            filename=download.filename,
            track_title=download.track_title,
            status=download.status,
            progress=download.progress,
            file_path=download.file_path,
            file_size=download.file_size,
            download_url=download.download_url,
            started_at=download.started_at,
            download_completed_at=download.download_completed_at,
            error_message=download.error_message,
            created_at=download.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting download: {e}")
        raise HTTPException(status_code=500, detail="Failed to get download")

@app.delete("/downloads/{download_id}")
async def cancel_download(
    download_id: str,
    current_user: dict = Depends(AuthDependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a download"""
    try:
        download_result = await db.execute(
            select(Download).where(
                Download.id == download_id,
                Download.user_id == current_user["user_id"]
            )
        )
        download = download_result.scalar_one_or_none()
        
        if not download:
            raise HTTPException(status_code=404, detail="Download not found")
        
        if download.status in ["completed", "failed"]:
            raise HTTPException(status_code=400, detail="Cannot cancel completed or failed download")
        
        # Update status to cancelled
        download.status = "cancelled"
        await db.commit()
        
        return {"message": "Download cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling download: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel download")

@app.get("/downloads/{download_id}/file")
async def download_file(
    download_id: str,
    current_user: dict = Depends(AuthDependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download/save a completed file to the user's system"""
    try:
        download_result = await db.execute(
            select(Download).where(
                Download.id == download_id,
                Download.user_id == current_user["user_id"]
            )
        )
        download = download_result.scalar_one_or_none()
        
        if not download:
            raise HTTPException(status_code=404, detail="Download not found")
        
        if download.status != "completed":
            raise HTTPException(status_code=400, detail="Download not completed yet")
        
        if not download.file_path or not os.path.exists(download.file_path):
            raise HTTPException(status_code=404, detail="File not found on server")
        
        # Return the file for download
        from fastapi.responses import FileResponse
        return FileResponse(
            path=download.file_path,
            filename=download.filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail="Failed to download file")

@app.websocket("/ws/downloads/{user_id}")
async def download_progress_websocket(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time download progress"""
    await websocket.accept()
    try:
        while True:
            # Send current download status
            async with AsyncSessionLocal() as db:
                downloads_result = await db.execute(
                    select(Download)
                    .where(Download.user_id == user_id)
                    .where(Download.status.in_(["pending", "downloading"]))
                )
                downloads = downloads_result.scalars().all()
                
                for download in downloads:
                    progress_message = DownloadProgress(
                        download_id=download.id,
                        progress=download.progress,
                        status=download.status,
                        message=f"Downloading {download.progress:.1f}%"
                    )
                    await websocket.send_json(progress_message.dict())
            
            await asyncio.sleep(2)  # Update every 2 seconds
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

async def process_download(download_id: str):
    """Background task to process a download"""
    try:
        # Update status to downloading
        await update_download_status(download_id, "downloading", progress=0.0)
        
        # Get download details
        async with AsyncSessionLocal() as db:
            download_result = await db.execute(
                select(Download).where(Download.id == download_id)
            )
            download = download_result.scalar_one_or_none()
            
            if not download:
                logger.error(f"Download {download_id} not found")
                return
        
        # Create user download directory
        user_download_dir = DOWNLOAD_DIR / download.user_id
        user_download_dir.mkdir(exist_ok=True)
        
        # Create archive-specific subdirectory
        archive_dir = user_download_dir / download.archive_identifier
        archive_dir.mkdir(exist_ok=True)
        
        # Download file
        file_path = archive_dir / download.filename
        
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            logger.info(f"Starting download for {download_id}: {download.download_url}")
            
            async with client.stream("GET", download.download_url) as response:
                response.raise_for_status()
                
                # Log the final URL after redirects
                final_url = str(response.url)
                if final_url != download.download_url:
                    logger.info(f"Download redirected from {download.download_url} to {final_url}")
                
                total_size = int(response.headers.get("content-length", 0))
                downloaded_size = 0
                
                async with aiofiles.open(file_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        await f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            await update_download_status(download_id, "downloading", progress=progress)
        
        # Update download as completed
        await update_download_status(
            download_id, 
            "completed", 
            progress=100.0,
            file_path=str(file_path),
            file_size=downloaded_size
        )
        
        logger.info(f"Download {download_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing download {download_id}: {e}")
        await update_download_status(download_id, "failed", error_message=str(e))

async def update_download_status(
    download_id: str,
    status: str,
    progress: float = 0.0,
    file_path: str = None,
    file_size: int = None,
    error_message: str = None
):
    """Update download status in database"""
    try:
        async with AsyncSessionLocal() as db:
            download = await db.execute(
                select(Download).where(Download.id == download_id)
            )
            download = download.scalar_one_or_none()
            
            if download:
                download.status = status
                download.progress = progress
                
                if file_path:
                    download.file_path = file_path
                if file_size:
                    download.file_size = file_size
                if error_message:
                    download.error_message = error_message
                
                if status == "downloading" and not download.started_at:
                    download.started_at = datetime.utcnow()
                elif status in ["completed", "failed"]:
                    download.download_completed_at = datetime.utcnow()
                
                await db.commit()
                
    except Exception as e:
        logger.error(f"Error updating download status: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

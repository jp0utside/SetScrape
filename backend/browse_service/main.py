import os
import asyncio
import logging
import json
import hashlib
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from datetime import datetime, timedelta
import httpx

from shared.database import get_db, init_db, close_db, AsyncSessionLocal
from shared.models import (
    ArchiveItem, ArchiveTrack, ArchiveSearchResponse, CacheEntryResponse,
    HealthCheckResponse, StatsResponse
)
from pydantic import BaseModel
from typing import Dict, Any
from shared.database_models import CacheEntry

# New models for directory browsing
class ArchiveFile(BaseModel):
    name: str  # Changed from filename to match frontend
    size: Optional[int] = None
    last_modified: Optional[str] = None
    type: str  # Changed from file_type to match frontend
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

# Internet Archive API configuration
IA_API_BASE = "https://archive.org/advancedsearch.php"
IA_METADATA_BASE = "https://archive.org/metadata"

# Cache configuration
CACHE_DURATION_MINUTES = {
    'search': 30,      # Search results cache for 30 minutes
    'metadata': 60,    # Item metadata cache for 1 hour
    'item': 120        # Full item data cache for 2 hours
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Browse Service...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down Browse Service...")
    await close_db()

# Create FastAPI app
app = FastAPI(
    title="Internet Archive Browse Service",
    description="Real-time browsing service for Internet Archive live music with smart caching",
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
        service="browse-service",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )

@app.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get browse service statistics"""
    try:
        # Get cache statistics
        cache_stats_result = await db.execute(select(func.count(CacheEntry.id)))
        total_cache_entries = cache_stats_result.scalar()
        
        # Get expired cache entries
        expired_cache_result = await db.execute(
            select(func.count(CacheEntry.id))
            .where(CacheEntry.expires_at < datetime.utcnow())
        )
        expired_cache_entries = expired_cache_result.scalar()
        
        # Get cache hit statistics
        cache_hits_result = await db.execute(
            select(func.sum(CacheEntry.access_count))
        )
        total_cache_hits = cache_hits_result.scalar() or 0
        
        return {
            "total_users": 0,  # Not tracked in browse service
            "total_downloads": 0,  # Not tracked in browse service
            "total_concerts": 0,  # Not tracked in browse service
            "total_recordings": 0,  # Not tracked in browse service
            "cache_stats": {
                "total_entries": total_cache_entries,
                "expired_entries": expired_cache_entries,
                "total_hits": total_cache_hits,
                "total_size_bytes": total_cache_hits * 1024,  # Estimate
                "cache_types": {
                    "search": CACHE_DURATION_MINUTES['search'],
                    "metadata": CACHE_DURATION_MINUTES['metadata'],
                    "item": CACHE_DURATION_MINUTES['item']
                }
            },
            "download_stats": {"status": "not_handled_by_browse_service"}
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")

@app.get("/browse", response_model=ArchiveSearchResponse)
async def browse_archive(
    query: Optional[str] = Query(None, description="Search query"),
    collection: str = Query("etree", description="Collection to browse"),
    exclude_collection: str = Query("stream_only", description="Collection to exclude"),
    date_range: Optional[str] = Query(None, description="Date range (e.g., '30d', '90d', '1y')"),
    artist: Optional[str] = Query(None, description="Filter by artist"),
    venue: Optional[str] = Query(None, description="Filter by venue"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query("relevance", description="Sort by field (date, addeddate, title, relevance)"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc, desc)"),
    db: AsyncSession = Depends(get_db)
):
    """Browse Internet Archive for live music"""
    try:
        # Build search query
        search_query = f'collection:{collection} AND NOT collection:{exclude_collection}'
        
        if query:
            search_query += f' AND ({query})'
        
        if date_range:
            end_date = datetime.utcnow()
            if date_range == '7d':
                start_date = end_date - timedelta(days=7)
            elif date_range == '30d':
                start_date = end_date - timedelta(days=30)
            elif date_range == '90d':
                start_date = end_date - timedelta(days=90)
            elif date_range == '1y':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)  # Default to 30 days
            
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            search_query += f' AND date:[{start_date_str} TO {end_date_str}]'
        
        if artist:
            search_query += f' AND creator:"{artist}"'
        
        if venue:
            search_query += f' AND venue:"{venue}"'
        
        # Check cache first
        cache_key = hashlib.md5(f"browse:{search_query}:{page}:{per_page}".encode()).hexdigest()
        cached_result = await get_cached_data(db, cache_key, 'search')
        
        if cached_result:
            logger.info(f"Cache hit for browse query: {search_query}")
            return cached_result
        
        # Build sorting parameters
        sort_field = sort_by if sort_by in ['date', 'addeddate', 'title', 'relevance'] else 'relevance'
        sort_direction = sort_order if sort_order in ['asc', 'desc'] else 'desc'
        
        # For Internet Archive, we need to use 'sort' parameter
        # If relevance is selected, don't add any sort parameters (use natural relevance order)
        if sort_field == 'relevance':
            sort_param = ""
        elif sort_field == 'date':
            sort_param = f"sort[0]=date+{sort_direction}&sort[1]=addeddate+desc"
        elif sort_field == 'addeddate':
            sort_param = f"sort[0]=addeddate+{sort_direction}"
        else:
            sort_param = f"sort[0]=title+{sort_direction}"
        
        # Query Internet Archive
        if sort_param:
            ia_url = f"{IA_API_BASE}?q={search_query}&output=json&rows={per_page}&page={page}&{sort_param}"
        else:
            ia_url = f"{IA_API_BASE}?q={search_query}&output=json&rows={per_page}&page={page}"
        logger.info(f"🌐 Querying Internet Archive: {ia_url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(ia_url)
            response.raise_for_status()
            
            data = response.json()
            docs = data.get("response", {}).get("docs", [])
            total = data.get("response", {}).get("numFound", 0)
            
            # Process results
            items = []
            for doc in docs:
                item = await process_archive_item(doc)
                if item:
                    items.append(item)
            
            # Create response
            result = ArchiveSearchResponse(
                total=total,
                page=page,
                per_page=per_page,
                total_pages=(total + per_page - 1) // per_page,
                results=items
            )
            
            # Cache the result
            await cache_data(db, cache_key, 'search', result.model_dump())
            
            logger.info(f"Browse query returned {len(items)} items from {total} total")
            return result
            
    except httpx.TimeoutException:
        logger.error("Timeout while querying Internet Archive")
        raise HTTPException(status_code=504, detail="Internet Archive request timeout")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from Internet Archive: {e}")
        raise HTTPException(status_code=502, detail="Internet Archive service error")
    except Exception as e:
        logger.error(f"Error browsing archive: {e}")
        raise HTTPException(status_code=500, detail="Failed to browse archive")

@app.get("/item/{identifier}", response_model=ArchiveItem)
async def get_item_details(
    identifier: str,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific Internet Archive item"""
    try:
        # Check cache first
        cache_key = hashlib.md5(f"item:{identifier}".encode()).hexdigest()
        cached_result = await get_cached_data(db, cache_key, 'item')
        
        if cached_result:
            logger.info(f"Cache hit for item: {identifier}")
            return cached_result
        
        # Get item metadata from Internet Archive
        metadata_url = f"{IA_METADATA_BASE}/{identifier}"
        logger.info(f"🌐 Getting item metadata: {metadata_url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(metadata_url)
            response.raise_for_status()
            
            metadata = response.json()
            
            # Process item details
            item = await process_item_metadata(identifier, metadata)
            
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            
            # Cache the result
            await cache_data(db, cache_key, 'item', item.model_dump())
            
            logger.info(f"Retrieved item details for: {identifier}")
            return item
            
    except httpx.TimeoutException:
        logger.error(f"Timeout while getting item details for {identifier}")
        raise HTTPException(status_code=504, detail="Internet Archive request timeout")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error getting item details: {e}")
        raise HTTPException(status_code=502, detail="Internet Archive service error")
    except Exception as e:
        logger.error(f"Error getting item details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get item details")

@app.get("/cache", response_model=List[CacheEntryResponse])
async def get_cache_entries(
    cache_type: Optional[str] = Query(None, description="Filter by cache type"),
    db: AsyncSession = Depends(get_db)
):
    """Get cache entries for monitoring"""
    try:
        query = select(CacheEntry)
        if cache_type:
            query = query.where(CacheEntry.cache_type == cache_type)
        
        result = await db.execute(query)
        entries = result.scalars().all()
        
        return [
            CacheEntryResponse(
                id=entry.id,
                cache_key=entry.cache_key,
                cache_type=entry.cache_type,
                expires_at=entry.expires_at,
                created_at=entry.created_at,
                last_accessed=entry.last_accessed,
                access_count=entry.access_count
            )
            for entry in entries
        ]
    except Exception as e:
        logger.error(f"Error getting cache entries: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache entries")

@app.delete("/cache")
async def clear_cache(
    cache_type: Optional[str] = Query(None, description="Clear specific cache type"),
    db: AsyncSession = Depends(get_db)
):
    """Clear cache entries"""
    try:
        if cache_type:
            await db.execute(
                select(CacheEntry).where(CacheEntry.cache_type == cache_type).delete()
            )
            logger.info(f"Cleared cache entries of type: {cache_type}")
        else:
            await db.execute(select(CacheEntry).delete())
            logger.info("Cleared all cache entries")
        
        await db.commit()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

# Helper functions
async def get_cached_data(db: AsyncSession, cache_key: str, cache_type: str):
    """Get cached data if it exists and is not expired"""
    try:
        result = await db.execute(
            select(CacheEntry)
            .where(
                and_(
                    CacheEntry.cache_key == cache_key,
                    CacheEntry.cache_type == cache_type,
                    CacheEntry.expires_at > datetime.utcnow()
                )
            )
        )
        entry = result.scalar_one_or_none()
        
        if entry:
            # Update access count and last accessed time
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
            await db.commit()
            
            return json.loads(entry.cache_data)
        
        return None
    except Exception as e:
        logger.error(f"Error getting cached data: {e}")
        return None

async def cache_data(db: AsyncSession, cache_key: str, cache_type: str, data: dict):
    """Cache data with appropriate expiration"""
    try:
        # Calculate expiration time
        duration_minutes = CACHE_DURATION_MINUTES.get(cache_type, 30)
        expires_at = datetime.utcnow() + timedelta(minutes=duration_minutes)
        
        # Create or update cache entry
        cache_entry = CacheEntry(
            cache_key=cache_key,
            cache_data=json.dumps(data),
            cache_type=cache_type,
            expires_at=expires_at
        )
        
        db.add(cache_entry)
        await db.commit()
        
        logger.info(f"Cached data for key: {cache_key}, type: {cache_type}")
    except Exception as e:
        logger.error(f"Error caching data: {e}")

async def process_archive_item(doc: dict) -> Optional[ArchiveItem]:
    """Process a single Internet Archive item from search results"""
    try:
        identifier = doc.get("identifier")
        if not identifier:
            return None
        
        # Extract basic information
        title = doc.get("title", "Unknown Title")
        artist = doc.get("creator")
        date_str = doc.get("date")
        
        # Parse date
        date = None
        if date_str:
            try:
                if len(str(date_str)) == 4:  # Just year
                    date = datetime.strptime(str(date_str), "%Y")
                elif len(str(date_str)) >= 10:  # Full date
                    date = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
            except ValueError:
                pass
        
        # Extract venue and location from title and description
        # Internet Archive doesn't have dedicated venue/location fields, so we need to parse them
        title_text = doc.get("title", "")
        description_text = doc.get("description", "")
        
        venue = None
        location = None
        
        # Extract venue and location from title
        # Pattern: "Artist Live at VENUE, LOCATION on DATE"
        import re
        
        # Simple approach: find everything between "at" and "on" (or end of string)
        at_pattern = r"(?:Live\s+)?at\s+(.+?)(?:\s+on\s+\d{4}-\d{2}-\d{2}|\s*$)"
        match = re.search(at_pattern, title_text, re.IGNORECASE)
        
        if match:
            venue_location_part = match.group(1).strip()
            
            # Split by first comma to separate venue and location
            if "," in venue_location_part:
                parts = venue_location_part.split(",", 1)
                venue = parts[0].strip()
                location = parts[1].strip()
            else:
                venue = venue_location_part
                location = None
        
        # If venue not found in title, try description
        if not venue and description_text:
            # Look for venue in description (often mentioned in first few lines)
            lines = description_text.split('\n')
            for line in lines[:3]:  # Check first 3 lines
                venue_match = re.search(r'([A-Z][a-z\s]+(?:Amphitheater|Theater|Arena|Stadium|Center|Hall|Club|Bar|Resort|Festival))', line)
                if venue_match:
                    venue = venue_match.group(1).strip()
                    break
        
        # Clean up venue name
        if venue:
            # Remove common suffixes and clean up
            venue = re.sub(r'\s+on\s+\d{4}-\d{2}-\d{2}$', '', venue)
            venue = re.sub(r'\s*-\s*[^-]+$', '', venue)  # Remove city/state suffix
            venue = venue.strip()
            
            # Remove common words that aren't part of venue name
            venue = re.sub(r'\b(?:Festival|Resort|Resort)\b', '', venue).strip()
        
        # Get file information
        files = doc.get("files", [])
        audio_files = [f for f in files if f.get("format") in ["VBR MP3", "Flac", "Ogg Vorbis", "WAVE"]]
        
        # Create tracks list
        tracks = []
        for file_info in audio_files[:10]:  # Limit to first 10 tracks for preview
            track = ArchiveTrack(
                title=file_info.get("title", file_info.get("name", "Unknown Track")),
                filename=file_info.get("name", ""),
                file_format=file_info.get("format"),
                file_size=file_info.get("size"),
                duration=file_info.get("length"),
                download_url=f"https://archive.org/download/{identifier}/{file_info.get('name', '')}"
            )
            tracks.append(track)
        
        return ArchiveItem(
            identifier=identifier,
            title=title,
            artist=artist,
            date=date,
            venue=venue,
            location=location,
            description=doc.get("description"),
            source=doc.get("source"),
            taper=doc.get("taper"),
            lineage=doc.get("lineage"),
            total_tracks=len(audio_files),
            total_size=sum(f.get("size", 0) for f in audio_files),
            tracks=tracks if tracks else None,
            # Add engagement statistics
            downloads=doc.get("downloads", 0)
        )
        
    except Exception as e:
        logger.error(f"Error processing archive item: {e}")
        return None

async def process_item_metadata(identifier: str, metadata: dict) -> Optional[ArchiveItem]:
    """Process detailed item metadata from Internet Archive"""
    try:
        files = metadata.get("files", [])
        audio_files = [f for f in files if f.get("format") in ["VBR MP3", "Flac", "Ogg Vorbis", "WAVE"]]
        
        # Extract metadata
        item_metadata = metadata.get("metadata", {})
        title = item_metadata.get("title", "Unknown Title")
        artist = item_metadata.get("creator")
        date_str = item_metadata.get("date")
        
        # Parse date
        date = None
        if date_str:
            try:
                if len(str(date_str)) == 4:  # Just year
                    date = datetime.strptime(str(date_str), "%Y")
                elif len(str(date_str)) >= 10:  # Full date
                    date = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
            except ValueError:
                pass
        
        # Create tracks list
        tracks = []
        for file_info in audio_files:
            track = ArchiveTrack(
                title=file_info.get("title", file_info.get("name", "Unknown Track")),
                filename=file_info.get("name", ""),
                file_format=file_info.get("format"),
                file_size=file_info.get("size"),
                duration=file_info.get("length"),
                download_url=f"https://archive.org/download/{identifier}/{file_info.get('name', '')}"
            )
            tracks.append(track)
        
        return ArchiveItem(
            identifier=identifier,
            title=title,
            artist=artist,
            date=date,
            venue=item_metadata.get("venue"),
            location=item_metadata.get("location"),
            description=item_metadata.get("description"),
            source=item_metadata.get("source"),
            taper=item_metadata.get("taper"),
            lineage=item_metadata.get("lineage"),
            total_tracks=len(audio_files),
            total_size=sum(f.get("size", 0) for f in audio_files),
            tracks=tracks
        )
        
    except Exception as e:
        logger.error(f"Error processing item metadata: {e}")
        return None

def categorize_file(filename: str, size: int = None) -> tuple[str, str]:
    """Categorize a file by its extension and determine file type"""
    filename_lower = filename.lower()
    
    # Audio files
    if filename_lower.endswith(('.flac', '.mp3', '.ogg', '.wav', '.m4a')):
        return 'audio', filename_lower.split('.')[-1]
    
    # Image files
    elif filename_lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        return 'image', filename_lower.split('.')[-1]
    
    # Metadata files
    elif filename_lower.endswith(('.txt', '.xml', '.json', '.ffp', '.torrent', '.sqlite')):
        return 'metadata', filename_lower.split('.')[-1]
    
    # Other files
    else:
        return 'other', filename_lower.split('.')[-1] if '.' in filename_lower else 'unknown'

@app.get("/directory/{identifier}", response_model=ArchiveDirectory)
async def get_directory_structure(
    identifier: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the directory structure and available files for an archive identifier"""
    try:
        logger.info(f"Fetching directory structure for {identifier}")
        
        # Fetch metadata from Internet Archive
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{IA_METADATA_BASE}/{identifier}")
            response.raise_for_status()
            metadata = response.json()
        
        files_data = metadata.get("files", [])
        logger.info(f"Found {len(files_data)} files for {identifier}")
        
        # Process files
        archive_files = []
        audio_files = []
        image_files = []
        metadata_files = []
        total_size = 0
        
        for file_info in files_data:
            filename = file_info.get("name", "")
            size_str = file_info.get("size", "0")
            last_modified = file_info.get("mtime")
            
            # Convert size to integer, defaulting to 0 if conversion fails
            try:
                size = int(size_str) if size_str else 0
            except (ValueError, TypeError):
                size = 0
            
            file_type, file_format = categorize_file(filename, size)
            
            archive_file = ArchiveFile(
                name=filename,
                size=size,
                last_modified=last_modified,
                type=file_type,
                format=file_format
            )
            
            archive_files.append(archive_file)
            total_size += size
            
            # Categorize files
            if file_type == 'audio':
                audio_files.append(archive_file)
            elif file_type == 'image':
                image_files.append(archive_file)
            elif file_type == 'metadata':
                metadata_files.append(archive_file)
        
        logger.info(f"Processed {len(audio_files)} audio files, {len(image_files)} image files, {len(metadata_files)} metadata files")
        
        # Create directory response
        directory = ArchiveDirectory(
            identifier=identifier,
            files=archive_files,
            total_files=len(archive_files),
            total_size=total_size,
            audio_files=audio_files,
            image_files=image_files,
            metadata_files=metadata_files
        )
        
        logger.info(f"Successfully created directory response for {identifier}")
        return directory
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching directory for {identifier}: {e}")
        raise HTTPException(status_code=404, detail=f"Archive identifier '{identifier}' not found")
    except Exception as e:
        logger.error(f"Error fetching directory structure for {identifier}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to fetch directory structure")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

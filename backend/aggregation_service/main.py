import os
import asyncio
import logging
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from collections import defaultdict

from shared.database import get_db, init_db, close_db
from shared.models import (
    ArchiveItem, ArchiveTrack, ArchiveSearchResponse, HealthCheckResponse, StatsResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service URLs
BROWSE_SERVICE_URL = os.getenv("BROWSE_SERVICE_URL", "http://127.0.0.1:8001")

# In-memory cache for browse results
browse_cache = {}
CACHE_DURATION = 300  # 5 minutes

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Aggregation Service...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down Aggregation Service...")
    await close_db()

# Create FastAPI app
app = FastAPI(
    title="Concert Aggregation Service",
    description="Intelligent aggregation layer that groups Internet Archive recordings by concert instances with smart caching",
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

def extract_concert_key(item: ArchiveItem) -> str:
    """Extract a unique concert key from an archive item"""
    artist = item.artist or "Unknown Artist"
    
    if item.date:
        if hasattr(item.date, 'strftime'):
            date_str = item.date.strftime("%Y-%m-%d")
        else:
            date_str = str(item.date)[:10]  # Take first 10 chars for YYYY-MM-DD
    else:
        date_str = "unknown"
    
    # Only use artist and date for grouping - omit venue to group recordings properly
    return f"{artist}|{date_str}"

def group_recordings_by_concert(items: List[ArchiveItem]) -> List[Dict[str, Any]]:
    """Group archive items by concert key and return concert instances"""
    concert_groups = defaultdict(list)
    
    # Group items by concert key
    for item in items:
        key = extract_concert_key(item)
        concert_groups[key].append(item)
    
    # Create concert instances
    concerts = []
    for key, recordings in concert_groups.items():
        if not recordings:
            continue
            
        # Parse concert key
        parts = key.split("|")
        if len(parts) != 2:
            continue
            
        artist, date_str = parts
        
        try:
            concert_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue
        
        # Use first recording for base metadata
        base_recording = recordings[0]
        
        # Determine venue from recordings (use the most common venue if multiple exist)
        venue_counts = {}
        for recording in recordings:
            if recording.venue and recording.venue != "Unknown Venue":
                venue_counts[recording.venue] = venue_counts.get(recording.venue, 0) + 1
        
        # Use the most common venue, or the first non-unknown venue, or None
        venue = None
        if venue_counts:
            venue = max(venue_counts, key=venue_counts.get)
        else:
            # Look for any non-unknown venue
            for recording in recordings:
                if recording.venue and recording.venue != "Unknown Venue":
                    venue = recording.venue
                    break
        
        # Format title as ARTIST-VENUE-LOCATION (omit venue if missing or unknown)
        title_parts = [artist]
        if venue:
            title_parts.append(venue)
        if base_recording.location:
            title_parts.append(base_recording.location)
        title = "-".join(title_parts)
        
        description = base_recording.description or f"Live performance by {artist}"
        source = base_recording.source or "Multiple sources available"
        taper = base_recording.taper or None
        lineage = base_recording.lineage or None
        
        # Create concert instance
        concert = {
            "id": key,  # Use concert_key as id for frontend compatibility
            "concert_key": key,
            "artist": artist,
            "date": concert_date,
            "venue": venue,
            "location": base_recording.location,
            "title": title,
            "description": description,
            "source": source,
            "taper": taper,
            "lineage": lineage,
            "total_recordings": len(recordings),
            "total_tracks": sum(r.total_tracks for r in recordings),
            "total_size": sum(r.total_size for r in recordings),
            "total_downloads": sum(r.downloads for r in recordings),
            "indexed_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "recordings": [
                {
                    "id": r.identifier,  # Use identifier as id for frontend compatibility
                    "archive_identifier": r.identifier,
                    "title": r.title,
                    "description": r.description,
                    "source": r.source,
                    "taper": r.taper,
                    "lineage": r.lineage,
                    "total_tracks": r.total_tracks,
                    "total_size": r.total_size,
                    "tracks": r.tracks,
                    "downloads": r.downloads,  # Add download count
                    "created_at": datetime.utcnow().isoformat()  # Add required field
                }
                for r in recordings
            ]
        }
        concerts.append(concert)
    
    return concerts

def get_cache_key(params: Dict[str, Any]) -> str:
    """Generate a cache key from request parameters"""
    # Sort parameters for consistent cache keys
    sorted_params = sorted(params.items())
    return json.dumps(sorted_params)

def is_cache_valid(cache_entry: Dict[str, Any]) -> bool:
    """Check if cache entry is still valid"""
    if not cache_entry:
        return False
    
    cache_time = cache_entry.get("timestamp", 0)
    return (datetime.utcnow().timestamp() - cache_time) < CACHE_DURATION

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(
        status="healthy",
        service="aggregation-service",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )

@app.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get service statistics"""
    try:
        cache_size = len(browse_cache)
        cache_entries = sum(1 for entry in browse_cache.values() if is_cache_valid(entry))
        
        return StatsResponse(
            total_users=0,
            total_downloads=0,
            total_concerts=0,
            total_recordings=0,
            cache_stats={
                "cache_size": cache_size,
                "valid_entries": cache_entries,
                "cache_duration_seconds": CACHE_DURATION
            },
            download_stats={}
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")

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
    db: AsyncSession = Depends(get_db)
):
    """Browse concerts (grouped recordings) from Internet Archive with smart caching"""
    try:
        # Build parameters for browse service
        params = {
            "query": query,
            "date_range": date_range,
            "artist": artist,
            "venue": venue,
            "page": page,
            "per_page": per_page * 3,  # Get more recordings to account for grouping
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        # Check cache first
        cache_key = get_cache_key(params)
        cache_entry = browse_cache.get(cache_key)
        
        if is_cache_valid(cache_entry):
            logger.info(f"Using cached data for key: {cache_key[:50]}...")
            concerts = cache_entry["data"]
        else:
            logger.info(f"Fetching fresh data with params: {params}")
            
            # Fetch from browse service
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{BROWSE_SERVICE_URL}/browse", params=params)
                response.raise_for_status()
                browse_data = response.json()
            
            # Parse archive items
            raw_items = [ArchiveItem(**item) for item in browse_data.get("results", [])]
            logger.info(f"Fetched {len(raw_items)} recordings from browse service")
            
            # Group by concert
            concerts = group_recordings_by_concert(raw_items)
            logger.info(f"Grouped into {len(concerts)} concerts")
            
            # Filter by concert date if date_range is specified and filter_by_concert_date is True
            if date_range and filter_by_concert_date:
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
                
                # Filter concerts by their actual concert date
                filtered_concerts = []
                for concert in concerts:
                    concert_date = concert["date"]
                    if isinstance(concert_date, str):
                        concert_date = datetime.fromisoformat(concert_date.replace('Z', '+00:00'))
                    elif hasattr(concert_date, 'date'):
                        concert_date = concert_date
                    else:
                        continue
                    
                    if start_date <= concert_date <= end_date:
                        filtered_concerts.append(concert)
                
                concerts = filtered_concerts
                logger.info(f"Filtered to {len(concerts)} concerts within concert date range")
            elif date_range and not filter_by_concert_date:
                # Keep upload date filtering from browse service
                logger.info(f"Using upload date filtering from browse service")
            
            # Cache the results
            browse_cache[cache_key] = {
                "data": concerts,
                "timestamp": datetime.utcnow().timestamp(),
                "raw_items": raw_items  # Store raw items for concert details
            }
            
            # Clean up old cache entries
            cleanup_cache()
        
        # Sort concerts based on parameters
        if sort_by == "date":
            concerts.sort(key=lambda x: x["date"], reverse=(sort_order == "desc"))
        elif sort_by == "artist":
            concerts.sort(key=lambda x: x["artist"].lower(), reverse=(sort_order == "desc"))
        elif sort_by == "venue":
            concerts.sort(key=lambda x: (x["venue"] or "").lower(), reverse=(sort_order == "desc"))
        else:
            # Default to date sorting
            concerts.sort(key=lambda x: x["date"], reverse=(sort_order == "desc"))
        
        # Apply pagination to concerts
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_concerts = concerts[start_idx:end_idx]
        
        return {
            "total": len(concerts),
            "page": page,
            "per_page": per_page,
            "total_pages": (len(concerts) + per_page - 1) // per_page,
            "results": paginated_concerts
        }
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Browse service error: {e}")
        raise HTTPException(status_code=502, detail="Browse service unavailable")
    except Exception as e:
        logger.error(f"Error aggregating concerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to aggregate concerts")

@app.get("/concerts/{concert_key}")
async def get_concert_details(
    concert_key: str,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific concert from cache"""
    try:
        # Find the concert in our cache
        concert = None
        for cache_entry in browse_cache.values():
            if not is_cache_valid(cache_entry):
                continue
                
            for cached_concert in cache_entry["data"]:
                if cached_concert["concert_key"] == concert_key:
                    concert = cached_concert
                    break
            
            if concert:
                break
        
        if not concert:
            # If not in cache, we need to search for it
            logger.info(f"Concert {concert_key} not in cache, searching...")
            
            # Parse concert key to get search parameters
            parts = concert_key.split("|")
            if len(parts) != 2:
                raise HTTPException(status_code=400, detail="Invalid concert key format")
            
            artist, date_str = parts
            
            # Search for this specific concert
            params = {
                "artist": artist,
                "per_page": 100  # Get more recordings to ensure we find the concert
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{BROWSE_SERVICE_URL}/browse", params=params)
                response.raise_for_status()
                browse_data = response.json()
            
            # Parse and group recordings
            raw_items = [ArchiveItem(**item) for item in browse_data.get("results", [])]
            
            # Filter for the specific date
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                matching_items = []
                for item in raw_items:
                    if item.date:
                        item_date = item.date
                        if hasattr(item_date, 'date'):
                            item_date = item_date.date()
                        elif isinstance(item_date, str):
                            try:
                                item_date = datetime.strptime(item_date, "%Y-%m-%d").date()
                            except ValueError:
                                continue
                        
                        if item_date == target_date:
                            matching_items.append(item)
                
                if not matching_items:
                    raise HTTPException(status_code=404, detail="Concert not found")
                
                # Group the matching items
                concerts = group_recordings_by_concert(matching_items)
                concert = next((c for c in concerts if c["concert_key"] == concert_key), None)
                
                if not concert:
                    raise HTTPException(status_code=404, detail="Concert not found")
                    
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format")
        
        return concert
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting concert details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get concert details")

def cleanup_cache():
    """Remove expired cache entries"""
    current_time = datetime.utcnow().timestamp()
    expired_keys = [
        key for key, entry in browse_cache.items()
        if (current_time - entry.get("timestamp", 0)) >= CACHE_DURATION
    ]
    
    for key in expired_keys:
        del browse_cache[key]
    
    if expired_keys:
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

@app.delete("/cache")
async def clear_cache():
    """Clear all cached data"""
    global browse_cache
    cache_size = len(browse_cache)
    browse_cache = {}
    logger.info(f"Cleared {cache_size} cache entries")
    return {"message": f"Cleared {cache_size} cache entries"}

@app.get("/cache")
async def get_cache_info():
    """Get cache information"""
    current_time = datetime.utcnow().timestamp()
    valid_entries = sum(1 for entry in browse_cache.values() if is_cache_valid(entry))
    expired_entries = len(browse_cache) - valid_entries
    
    return {
        "total_entries": len(browse_cache),
        "valid_entries": valid_entries,
        "expired_entries": expired_entries,
        "cache_duration_seconds": CACHE_DURATION
    }

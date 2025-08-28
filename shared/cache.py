import asyncio
import json
import pickle
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import threading
import time

class InMemoryCache:
    """Simple in-memory cache to replace Redis for local development"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task to clean expired keys"""
        def cleanup_loop():
            while True:
                time.sleep(60)  # Clean every minute
                self._cleanup_expired()
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_expired(self):
        """Remove expired keys from cache"""
        current_time = datetime.utcnow()
        with self._lock:
            expired_keys = [
                key for key, value in self._cache.items()
                if value.get('expires_at') and current_time > value['expires_at']
            ]
            for key in expired_keys:
                del self._cache[key]
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set a key-value pair with optional expiration (seconds)"""
        try:
            with self._lock:
                cache_entry = {
                    'value': value,
                    'created_at': datetime.utcnow()
                }
                if expire:
                    cache_entry['expires_at'] = datetime.utcnow() + timedelta(seconds=expire)
                
                self._cache[key] = cache_entry
                return True
        except Exception:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value for a key"""
        try:
            with self._lock:
                if key not in self._cache:
                    return None
                
                entry = self._cache[key]
                
                # Check if expired
                if entry.get('expires_at') and datetime.utcnow() > entry['expires_at']:
                    del self._cache[key]
                    return None
                
                return entry['value']
        except Exception:
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key"""
        try:
            with self._lock:
                if key in self._cache:
                    del self._cache[key]
                    return True
                return False
        except Exception:
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        return self.get(key) is not None
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for a key"""
        try:
            with self._lock:
                if key in self._cache:
                    self._cache[key]['expires_at'] = datetime.utcnow() + timedelta(seconds=seconds)
                    return True
                return False
        except Exception:
            return False
    
    def ttl(self, key: str) -> int:
        """Get time to live for a key in seconds"""
        try:
            with self._lock:
                if key not in self._cache:
                    return -2  # Key doesn't exist
                
                entry = self._cache[key]
                if not entry.get('expires_at'):
                    return -1  # No expiration
                
                ttl = (entry['expires_at'] - datetime.utcnow()).total_seconds()
                return max(0, int(ttl))
        except Exception:
            return -2
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern (simple glob support)"""
        try:
            with self._lock:
                if pattern == "*":
                    return list(self._cache.keys())
                
                # Simple pattern matching
                import fnmatch
                return [key for key in self._cache.keys() if fnmatch.fnmatch(key, pattern)]
        except Exception:
            return []
    
    def flush(self) -> bool:
        """Clear all keys"""
        try:
            with self._lock:
                self._cache.clear()
                return True
        except Exception:
            return False
    
    def info(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            with self._lock:
                total_keys = len(self._cache)
                expired_keys = len([
                    key for key, value in self._cache.items()
                    if value.get('expires_at') and datetime.utcnow() > value['expires_at']
                ])
                
                return {
                    'total_keys': total_keys,
                    'expired_keys': expired_keys,
                    'active_keys': total_keys - expired_keys,
                    'memory_usage': 'N/A'  # Not tracking memory usage for simplicity
                }
        except Exception:
            return {}

# Global cache instance
cache = InMemoryCache()

# Redis-compatible interface
class RedisClient:
    """Redis-compatible client using in-memory cache"""
    
    def __init__(self):
        self._cache = cache
    
    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set key-value pair"""
        return self._cache.set(key, value, ex)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value for key"""
        return self._cache.get(key)
    
    async def delete(self, key: str) -> bool:
        """Delete key"""
        return self._cache.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return self._cache.exists(key)
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        return self._cache.expire(key, seconds)
    
    async def ttl(self, key: str) -> int:
        """Get time to live for key"""
        return self._cache.ttl(key)
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        return self._cache.keys(pattern)
    
    async def flushdb(self) -> bool:
        """Clear all keys"""
        return self._cache.flush()
    
    async def info(self) -> Dict[str, Any]:
        """Get cache info"""
        return self._cache.info()

# Factory function to create Redis client
def create_redis_client() -> RedisClient:
    """Create a Redis-compatible client"""
    return RedisClient()

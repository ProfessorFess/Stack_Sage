"""
Meta Data Cache

Simple in-memory cache with TTL for metagame information.
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class CacheEntry:
    """A cached metagame entry."""
    data: Dict[str, Any]
    timestamp: float
    ttl_seconds: int = 86400  # 24 hours default
    
    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        return time.time() - self.timestamp > self.ttl_seconds
    
    def age_hours(self) -> float:
        """Get the age of this entry in hours."""
        return (time.time() - self.timestamp) / 3600
    
    def is_stale(self, stale_threshold_hours: float = 168) -> bool:
        """Check if data is stale (default: 7 days)."""
        return self.age_hours() > stale_threshold_hours


class MetaCache:
    """In-memory cache for metagame data with TTL."""
    
    def __init__(self, default_ttl: int = 86400):
        """
        Initialize the meta cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 24 hours)
        """
        self.cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a cached entry if it exists and hasn't expired.
        
        Args:
            key: Cache key (e.g., "standard_meta", "modern_meta")
            
        Returns:
            Cached data or None if not found/expired
        """
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        if entry.is_expired():
            print(f"[MetaCache] Entry '{key}' expired, removing")
            del self.cache[key]
            return None
        
        print(f"[MetaCache] Cache hit for '{key}' (age: {entry.age_hours():.1f}h)")
        return entry.data
    
    def set(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None):
        """
        Store data in the cache.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        ttl = ttl or self.default_ttl
        
        self.cache[key] = CacheEntry(
            data=data,
            timestamp=time.time(),
            ttl_seconds=ttl
        )
        
        print(f"[MetaCache] Cached '{key}' (TTL: {ttl/3600:.1f}h)")
    
    def is_stale(self, key: str, stale_threshold_hours: float = 168) -> bool:
        """
        Check if cached data is stale (old but not expired).
        
        Args:
            key: Cache key
            stale_threshold_hours: Hours after which data is considered stale (default: 7 days)
            
        Returns:
            True if data exists but is stale
        """
        if key not in self.cache:
            return False
        
        entry = self.cache[key]
        return entry.is_stale(stale_threshold_hours)
    
    def clear(self, key: Optional[str] = None):
        """
        Clear cache entries.
        
        Args:
            key: Specific key to clear, or None to clear all
        """
        if key:
            if key in self.cache:
                del self.cache[key]
                print(f"[MetaCache] Cleared '{key}'")
        else:
            self.cache.clear()
            print("[MetaCache] Cleared all entries")
    
    def get_all_keys(self) -> list:
        """Get all cache keys."""
        return list(self.cache.keys())
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the cache state."""
        info = {
            "total_entries": len(self.cache),
            "entries": []
        }
        
        for key, entry in self.cache.items():
            info["entries"].append({
                "key": key,
                "age_hours": entry.age_hours(),
                "is_stale": entry.is_stale(),
                "is_expired": entry.is_expired()
            })
        
        return info


# Global cache instance
_meta_cache = MetaCache(default_ttl=86400)  # 24 hour TTL


def get_meta_cache() -> MetaCache:
    """Get the global meta cache instance."""
    return _meta_cache


def cache_meta_data(format_name: str, data: Dict[str, Any], ttl: Optional[int] = None):
    """
    Cache metagame data for a format.
    
    Args:
        format_name: Format name (e.g., "standard", "modern")
        data: Meta data to cache
        ttl: Optional TTL in seconds
    """
    cache = get_meta_cache()
    key = f"{format_name.lower()}_meta"
    cache.set(key, data, ttl)


def get_cached_meta(format_name: str) -> Optional[Dict[str, Any]]:
    """
    Get cached metagame data for a format.
    
    Args:
        format_name: Format name
        
    Returns:
        Cached meta data or None
    """
    cache = get_meta_cache()
    key = f"{format_name.lower()}_meta"
    return cache.get(key)


def is_meta_stale(format_name: str, stale_hours: float = 168) -> bool:
    """
    Check if cached meta data is stale.
    
    Args:
        format_name: Format name
        stale_hours: Hours threshold for staleness (default: 7 days)
        
    Returns:
        True if data is stale
    """
    cache = get_meta_cache()
    key = f"{format_name.lower()}_meta"
    return cache.is_stale(key, stale_hours)


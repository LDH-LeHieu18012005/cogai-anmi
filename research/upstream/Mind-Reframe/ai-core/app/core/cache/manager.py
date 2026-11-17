from typing import Optional, Any
from app.core.cache.base import BaseCache
from app.core.cache.memory import MemoryCache
from app.core.cache.redis import RedisCache
from app.config import settings
from app.utils.logger import logger

class CacheManager:
    """
    Manager để quản lý cache implementation
    """
    
    def __init__(self):
        self._cache: Optional[BaseCache] = None
        self._initialize_cache()
    
    def _initialize_cache(self):
        """Initialize cache based on settings"""
        if not settings.CACHE_ENABLED:
            logger.info("Cache disabled")
            return
        
        if settings.CACHE_TYPE == "redis":
            try:
                self._cache = RedisCache()
                logger.info("Using Redis cache")
            except Exception as e:
                logger.warning(f"Redis cache failed, falling back to memory: {e}")
                self._cache = MemoryCache()
        else:
            self._cache = MemoryCache()
            logger.info("Using memory cache")
    
    @property
    def cache(self) -> Optional[BaseCache]:
        """Get cache instance"""
        return self._cache
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from cache"""
        if not self._cache:
            return None
        return await self._cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set to cache"""
        if not self._cache:
            return False
        return await self._cache.set(key, value, ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete from cache"""
        if not self._cache:
            return False
        return await self._cache.delete(key)
    
    async def clear(self) -> bool:
        """Clear cache"""
        if not self._cache:
            return False
        return await self._cache.clear()
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self._cache:
            return False
        return await self._cache.exists(key)
    
    def generate_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key"""
        if not self._cache:
            return ""
        return self._cache.generate_key(prefix, **kwargs)
    
    async def get_stats(self):
        """Get cache statistics"""
        if not self._cache:
            return {"enabled": False}
        
        if hasattr(self._cache, 'get_stats'):
            return await self._cache.get_stats()
        return {"enabled": True}

# Singleton instance
cache_manager = CacheManager()
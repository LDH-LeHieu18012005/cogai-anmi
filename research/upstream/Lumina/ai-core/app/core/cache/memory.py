from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from cachetools import TTLCache
from app.core.cache.base import BaseCache
from app.config import settings
from app.utils.logger import logger

class MemoryCache(BaseCache):
    """
    In-memory cache implementation using cachetools
    """
    
    def __init__(self, max_size: int = None, ttl: int = None):
        """
        Initialize memory cache
        
        Args:
            max_size: Maximum number of items (default from settings)
            ttl: Default TTL in seconds (default from settings)
        """
        self.max_size = max_size or settings.CACHE_MAX_SIZE
        self.ttl = ttl or settings.CACHE_TTL
        
        # TTLCache từ cachetools - tự động xóa expired items
        self._cache: TTLCache = TTLCache(maxsize=self.max_size, ttl=self.ttl)
        
        logger.info(
            f"Memory cache initialized",
            extra={
                "max_size": self.max_size,
                "default_ttl": self.ttl
            }
        )
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value từ cache"""
        try:
            value = self._cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit: {key}")
            else:
                logger.debug(f"Cache miss: {key}")
            return value
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value vào cache"""
        try:
            # TTLCache không hỗ trợ custom TTL per item
            # Nếu cần custom TTL, phải tạo cache riêng
            self._cache[key] = value
            logger.debug(f"Cache set: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key từ cache"""
        try:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache delete: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear toàn bộ cache"""
        try:
            self._cache.clear()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check key tồn tại"""
        return key in self._cache
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "type": "memory",
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl": self.ttl
        }
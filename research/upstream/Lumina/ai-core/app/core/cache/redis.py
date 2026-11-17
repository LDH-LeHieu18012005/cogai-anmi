from typing import Optional, Any, Dict
import json
import redis.asyncio as redis
from app.core.cache.base import BaseCache
from app.config import settings
from app.utils.logger import logger

class RedisCache(BaseCache):
    """
    Redis cache implementation
    """
    
    def __init__(self):
        """Initialize Redis cache"""
        self.ttl = settings.CACHE_TTL
        self._client: Optional[redis.Redis] = None
    
    async def _get_client(self) -> redis.Redis:
        """Get hoặc create Redis client"""
        if self._client is None:
            try:
                self._client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True
                )
                # Test connection
                await self._client.ping()
                logger.info(
                    f"Redis cache initialized",
                    extra={
                        "host": settings.REDIS_HOST,
                        "port": settings.REDIS_PORT
                    }
                )
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                raise
        
        return self._client
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value từ Redis"""
        try:
            client = await self._get_client()
            value = await client.get(key)
            
            if value is not None:
                logger.debug(f"Redis cache hit: {key}")
                return json.loads(value)
            else:
                logger.debug(f"Redis cache miss: {key}")
                return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value vào Redis"""
        try:
            client = await self._get_client()
            ttl = ttl or self.ttl
            
            # Serialize value to JSON
            serialized = json.dumps(value)
            
            await client.setex(key, ttl, serialized)
            logger.debug(f"Redis cache set: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key từ Redis"""
        try:
            client = await self._get_client()
            result = await client.delete(key)
            logger.debug(f"Redis cache delete: {key}")
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear toàn bộ cache (FLUSHDB)"""
        try:
            client = await self._get_client()
            await client.flushdb()
            logger.info("Redis cache cleared")
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check key tồn tại"""
        try:
            client = await self._get_client()
            result = await client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis statistics"""
        try:
            client = await self._get_client()
            info = await client.info()
            return {
                "type": "redis",
                "connected": True,
                "keys": await client.dbsize(),
                "memory_used": info.get("used_memory_human"),
                "uptime": info.get("uptime_in_seconds")
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {"type": "redis", "connected": False, "error": str(e)}
    
    async def close(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            logger.info("Redis connection closed")
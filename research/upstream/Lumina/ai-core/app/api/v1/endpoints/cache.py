from fastapi import APIRouter, HTTPException, Depends
from app.core.cache.manager import cache_manager
from app.middleware.auth import optional_api_key
from app.utils.logger import logger

router = APIRouter()

@router.get(
    "/stats",
    summary="Get cache statistics",
    description="Lấy thông tin thống kê về cache"
)
async def get_cache_stats(api_key: str = Depends(optional_api_key)):
    """
    Get cache statistics
    
    Returns thông tin về:
    - Cache type (memory/redis)
    - Number of cached items
    - Memory usage (nếu Redis)
    - Etc.
    """
    try:
        stats = await cache_manager.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete(
    "/clear",
    summary="Clear cache",
    description="Xóa toàn bộ cache"
)
async def clear_cache(api_key: str = Depends(optional_api_key)):
    """
    Clear toàn bộ cache
    
    **Cảnh báo**: Thao tác này sẽ xóa tất cả cached responses
    """
    try:
        success = await cache_manager.clear()
        if success:
            logger.info("Cache cleared via API")
            return {
                "message": "Cache cleared successfully",
                "success": True
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete(
    "/delete/{key}",
    summary="Delete cache key",
    description="Xóa một cache key cụ thể"
)
async def delete_cache_key(key: str, api_key: str = Depends(optional_api_key)):
    """
    Delete một cache key cụ thể
    """
    try:
        success = await cache_manager.delete(key)
        if success:
            logger.info(f"Cache key deleted: {key}")
            return {
                "message": f"Cache key '{key}' deleted",
                "success": True
            }
        else:
            return {
                "message": f"Cache key '{key}' not found",
                "success": False
            }
    except Exception as e:
        logger.error(f"Failed to delete cache key: {e}")
        raise HTTPException(status_code=500, detail=str(e))
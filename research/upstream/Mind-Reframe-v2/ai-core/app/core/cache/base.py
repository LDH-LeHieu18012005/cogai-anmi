from abc import ABC, abstractmethod
from typing import Optional, Any
import hashlib
import json

class BaseCache(ABC):
    """
    Abstract base class cho cache implementations
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value từ cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value hoặc None
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value vào cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True nếu success
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete key từ cache
        
        Args:
            key: Cache key
            
        Returns:
            True nếu success
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """
        Clear toàn bộ cache
        
        Returns:
            True nếu success
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check xem key có tồn tại không
        
        Args:
            key: Cache key
            
        Returns:
            True nếu key exists
        """
        pass
    
    def generate_key(self, prefix: str, **kwargs) -> str:
        """
        Generate cache key từ parameters
        
        Args:
            prefix: Key prefix
            **kwargs: Parameters to include in key
            
        Returns:
            Generated cache key
        """
        # Sort kwargs để đảm bảo consistent key
        sorted_params = json.dumps(kwargs, sort_keys=True)
        
        # Hash parameters
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()
        
        return f"{prefix}:{param_hash}"
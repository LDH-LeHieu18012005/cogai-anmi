from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GROQ_BASE_URL: Optional[str] = None
    
    # App Settings
    APP_NAME: str = "AI-Core API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Authentication
    AUTH_ENABLED: bool = False
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_KEYS: list[str] = ["demo-key-123", "test-key-456"]
    
    # Caching
    CACHE_ENABLED: bool = True
    CACHE_TYPE: str = "memory"  # "memory" hoặc "redis"
    CACHE_TTL: int = 3600  # Time to live in seconds (1 hour)
    CACHE_MAX_SIZE: int = 1000  # Max items in memory cache
    
    # Redis (nếu dùng Redis cache)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Response Compression
    COMPRESSION_ENABLED: bool = True
    COMPRESSION_MIN_SIZE: int = 500  # Minimum response size to compress (bytes)
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
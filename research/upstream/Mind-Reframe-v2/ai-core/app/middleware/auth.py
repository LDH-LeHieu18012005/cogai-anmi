from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.config import settings
from app.utils.logger import logger

# API Key Authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify API key từ header
    
    Args:
        api_key: API key từ X-API-Key header
        
    Returns:
        API key nếu valid
        
    Raises:
        HTTPException: Nếu API key invalid
    """
    if not settings.AUTH_ENABLED:
        return "auth-disabled"
    
    if not api_key:
        logger.warning("API request without API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key not in settings.API_KEYS:
        logger.warning(
            f"Invalid API key attempted",
            extra={"api_key_prefix": api_key[:8] + "..."}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    logger.info(
        f"API key verified",
        extra={"api_key_prefix": api_key[:8] + "..."}
    )
    
    return api_key

# Bearer Token Authentication (for future JWT support)
bearer_scheme = HTTPBearer(auto_error=False)

async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[str]:
    """
    Verify bearer token (JWT)
    
    Args:
        credentials: Bearer token credentials
        
    Returns:
        Token payload nếu valid
        
    Raises:
        HTTPException: Nếu token invalid
    """
    if not settings.AUTH_ENABLED:
        return None
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Implement JWT token verification
    # For now, just return the token
    return credentials.credentials

# Optional authentication (không bắt buộc)
async def optional_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """
    Optional API key verification
    Không raise error nếu không có key
    """
    if not settings.AUTH_ENABLED:
        return None
    
    if not api_key:
        return None
    
    if api_key in settings.API_KEYS:
        return api_key
    
    return None
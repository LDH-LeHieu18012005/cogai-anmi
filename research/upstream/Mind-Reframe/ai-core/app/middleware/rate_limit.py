from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from app.config import settings
from app.utils.logger import logger

# Tạo limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.RATE_LIMIT_ENABLED,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"]
)

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler khi vượt quá rate limit
    """
    logger.warning(
        f"Rate limit exceeded",
        extra={
            "client": get_remote_address(request),
            "path": request.url.path,
            "limit": exc.detail
        }
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "code": "RATE_LIMIT_EXCEEDED",
            "detail": f"Too many requests. Please try again later.",
            "retry_after": "60 seconds"
        },
        headers={
            "Retry-After": "60"
        }
    )
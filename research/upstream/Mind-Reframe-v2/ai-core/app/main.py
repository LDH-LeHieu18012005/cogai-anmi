from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.utils.errors import AIException
from app.models.responses import ErrorResponse
from app.api.v1.router import api_router
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.utils.logger import logger

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    description="""
    # AI-Core API
    
    API for LLM integration with support for multiple providers and prompt templates.
    
    ## Features
    
    * **Multiple LLM Providers**: OpenAI, Anthropic (coming soon)
    * **Chat & Completion**: Support for both conversational and completion endpoints
    * **Streaming**: Real-time streaming responses
    * **Prompt Templates**: Pre-built and custom prompt templates
    * **Template Management**: Create, list, and execute prompt templates
    * **Rate Limiting**: Automatic rate limiting to prevent abuse
    * **Authentication**: API key-based authentication (optional)
    
    ## Authentication
    
    When authentication is enabled, include your API key in the request header:
```
    X-API-Key: your-api-key-here
```
    
    ## Rate Limits
    
    * Default: 60 requests per minute per IP
    * Hourly: 1000 requests per hour per IP
    
    Response headers will include rate limit information:
    * `X-RateLimit-Limit`: Maximum requests allowed
    * `X-RateLimit-Remaining`: Remaining requests
    * `X-RateLimit-Reset`: Time when limit resets
    
    ## Support
    
    For issues or questions, please contact the development team.
    """,
    contact={
        "name": "AI-Core Team",
        "email": "support@ai-core.com",
    },
    license_info={
        "name": "MIT",
    }
)

# Add rate limiter to app state
app.state.limiter = limiter

# Add rate limit exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Logging Middleware (đầu tiên)
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(AIException)
async def ai_exception_handler(request: Request, exc: AIException):
    """Handle custom AI exceptions"""
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error=exc.message,
            code=exc.code,
            detail=exc.detail
        ).model_dump()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            code="INTERNAL_ERROR",
            detail=str(exc) if settings.DEBUG else None
        ).model_dump()
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Actions on startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Server: {settings.HOST}:{settings.PORT}")
    logger.info(f"Rate limiting: {'Enabled' if settings.RATE_LIMIT_ENABLED else 'Disabled'}")
    logger.info(f"Authentication: {'Enabled' if settings.AUTH_ENABLED else 'Disabled'}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Actions on shutdown"""
    logger.info(f"Shutting down {settings.APP_NAME}")

# Mount API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
@limiter.limit("10/minute")  # Rate limit cho root endpoint
async def root(request: Request):
    """Root endpoint with rate limiting"""
    logger.debug("Root endpoint accessed")
    return {
        "message": "Welcome to AI-Core API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api_v1": "/api/v1",
        "rate_limit": {
            "enabled": settings.RATE_LIMIT_ENABLED,
            "per_minute": settings.RATE_LIMIT_PER_MINUTE
        },
        "auth": {
            "enabled": settings.AUTH_ENABLED,
            "type": "API Key" if settings.AUTH_ENABLED else None
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
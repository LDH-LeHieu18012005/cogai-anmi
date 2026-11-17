from typing import Optional
import traceback
from app.utils.logger import logger

class AIException(Exception):
    """Base exception cho AI-related errors"""
    def __init__(
        self, 
        message: str, 
        code: str = "AI_ERROR", 
        detail: Optional[str] = None,
        log_traceback: bool = True
    ):
        self.message = message
        self.code = code
        self.detail = detail
        super().__init__(self.message)
        
        # Log error
        if log_traceback:
            logger.error(
                f"[{code}] {message}",
                extra={"detail": detail},
                exc_info=True
            )

class InvalidProviderError(AIException):
    """Exception khi provider không hợp lệ"""
    def __init__(self, provider: str):
        super().__init__(
            message=f"Invalid provider: {provider}",
            code="INVALID_PROVIDER",
            detail=f"Provider '{provider}' is not supported"
        )

class APIKeyError(AIException):
    """Exception khi API key không hợp lệ hoặc missing"""
    def __init__(self, provider: str):
        super().__init__(
            message=f"API key error for provider: {provider}",
            code="INVALID_API_KEY",
            detail=f"API key for '{provider}' is missing or invalid"
        )

class LLMResponseError(AIException):
    """Exception khi LLM response có lỗi"""
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=message,
            code="LLM_RESPONSE_ERROR",
            detail=detail
        )

class PromptTemplateError(AIException):
    """Exception liên quan đến prompt templates"""
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=message,
            code="PROMPT_TEMPLATE_ERROR",
            detail=detail
        )

class RateLimitError(AIException):
    """Exception khi vượt quá rate limit"""
    def __init__(self, message: str = "Rate limit exceeded", detail: Optional[str] = None):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            detail=detail,
            log_traceback=False  # Rate limit không cần log traceback
        )

class ValidationError(AIException):
    """Exception cho validation errors"""
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            detail=detail,
            log_traceback=False
        )
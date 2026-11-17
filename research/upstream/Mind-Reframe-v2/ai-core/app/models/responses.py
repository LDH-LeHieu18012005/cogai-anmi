from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class Usage(BaseModel):
    prompt_tokens: int = Field(..., description="Number of Tokens in prompt")
    completion_tokens: int = Field(..., description="Number of Tokens in completion")
    total_tokens: int = Field(..., description="Total tokens")

class ChatResponse(BaseModel):
    id: str = Field(..., description="Unique ID of response")
    content: str = Field(..., description="Content response from LLM")
    model: str = Field(..., description="Model used")
    provider: str = Field(..., description="Provider used")
    usage: Optional[Usage] = Field(None, description="Usage tokens Information")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp generate response")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "chatcmpl-123456",
                "content": "Xin chào! Tôi là AI assistant, tôi khỏe. Bạn thế nào?",
                "model": "gpt-3.5-turbo",
                "provider": "openai",
                "usage": {
                    "prompt_tokens": 20,
                    "completion_tokens": 30,
                    "total_tokens": 50
                },
                "created_at": "2024-01-01T10:00:00"
            }
        }

class CompletionResponse(BaseModel):
    """Response model cho completion endpoint"""
    id: str = Field(..., description="Unique ID của response")
    text: str = Field(..., description="Text completion từ LLM")
    model: str = Field(..., description="Model đã sử dụng")
    provider: str = Field(..., description="Provider đã sử dụng")
    usage: Optional[Usage] = Field(None, description="Thông tin usage tokens")
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "cmpl-789012",
                "text": "AI (Artificial Intelligence) là...",
                "model": "gpt-3.5-turbo",
                "provider": "openai",
                "usage": {
                    "prompt_tokens": 15,
                    "completion_tokens": 100,
                    "total_tokens": 115
                },
                "created_at": "2024-01-01T10:00:00"
            }
        }

class ErrorResponse(BaseModel):
    """Response model cho error"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Chi tiết lỗi")
    code: Optional[str] = Field(None, description="Error code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid API key",
                "detail": "The provided API key is invalid or expired",
                "code": "INVALID_API_KEY"
            }
        }

class HealthResponse(BaseModel):
    """Response model cho health check"""
    status: str = Field(..., description="Status của service")
    version: str = Field(..., description="Version của API")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2024-01-01T10:00:00"
            }
        }
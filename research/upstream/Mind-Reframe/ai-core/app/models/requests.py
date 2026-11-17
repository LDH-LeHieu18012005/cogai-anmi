from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class LLMProvider(str, Enum):
    OPENAI = "openai"
    GROQ = "groq"

class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class Message(BaseModel):
    role: MessageRole
    content: str

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Hello, how are you?"
            }
        }

class ChatRequest(BaseModel):
    messages: List[Message] = Field(
        ...,
        description = "List các message trong conversation",
        min_length = 1
    )

    provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="LLM provider để sử dụng"
    )

    model: Optional[str] = Field(
        default=None,
        description="Model cụ thể"
    )

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Creativity level of the response (0-2)"
    )

    max_tokens: Optional[int] = Field(
        default=1000,
        ge=1,
        le=4000,
        description="Max token in the response (1-4000)"
    )

    stream: bool = Field(
        default=False,
        description="Enable streaming response"
    )

    class Config:
        json_schoma_extra = {
            "example": {
                "messages": [
                    {"rold": "user", "content": "Hello, how are you?"}
                ],
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.5,
                "max_tokens": 1000,
                # "stream": True
            }
        }

class CompletionRequest(BaseModel):
    prompt: str = Field(
        ...,
        description="Prompt text to generate completion",
        min_length=1
    )

    provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="LLM provider để sử dụng"
    )

    model: Optional[str] = Field(
        default=None,
        description="Model cụ thể"
    )

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0
    )

    max_tokens: Optional[int] = Field(
        default=500,
        ge=1,
        le=4000
    )

    system_prompt: Optional[str] = Field(
        default=None,
        description="System prompt để định hướng behavior"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Viết một đoạn giới thiệu về AI",
                "provider": "openai",
                "temperature": 0.5,
                "max_tokens": 1000,
                "system_prompt": "Bạn là một chuyên gia về AI"
            }
        }
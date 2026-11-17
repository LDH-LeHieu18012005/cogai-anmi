from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.models.requests import LLMProvider

class PromptTemplateListRequest(BaseModel):
    """Request model để list templates"""
    category: Optional[str] = Field(
        default=None,
        description="Filter theo category (chat, summarization, extraction)"
    )

class PromptFormatRequest(BaseModel):
    """Request model để format một prompt template"""
    template_name: str = Field(
        ...,
        description="Tên của template (vd: chat.general, summarization.text)"
    )
    variables: Dict[str, Any] = Field(
        ...,
        description="Variables để fill vào template"
    )
    provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="LLM provider để sử dụng"
    )
    model: Optional[str] = Field(
        default=None,
        description="Model cụ thể (optional)"
    )
    override_temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Override temperature mặc định của template"
    )
    override_max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        le=4000,
        description="Override max_tokens mặc định của template"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "template_name": "chat.customer_support",
                "variables": {
                    "customer_name": "Nguyễn Văn A",
                    "issue": "Không thể đăng nhập",
                    "details": "Quên mật khẩu"
                },
                "provider": "openai",
                "model": "gpt-3.5-turbo"
            }
        }

class CustomTemplateRequest(BaseModel):
    """Request model để tạo custom template"""
    template_name: str = Field(
        ...,
        description="Tên cho custom template (format: custom.your_name)"
    )
    template: str = Field(
        ...,
        description="Template string với placeholders {variable}"
    )
    required_vars: Optional[list[str]] = Field(
        default=None,
        description="List các biến bắt buộc"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Default temperature"
    )
    max_tokens: int = Field(
        default=1000,
        ge=1,
        le=4000,
        description="Default max_tokens"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="System prompt (optional)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "template_name": "custom.my_template",
                "template": "Xin chào {name}, hôm nay là {date}",
                "required_vars": ["name", "date"],
                "temperature": 0.8,
                "max_tokens": 500,
                "system_prompt": "Bạn là một trợ lý thân thiện"
            }
        }

class PromptExecuteRequest(BaseModel):
    """Request model để execute prompt template (format + call LLM)"""
    template_name: str = Field(
        ...,
        description="Tên của template"
    )
    variables: Dict[str, Any] = Field(
        ...,
        description="Variables để fill vào template"
    )
    provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="LLM provider"
    )
    model: Optional[str] = Field(
        default=None,
        description="Model cụ thể"
    )
    override_temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Override temperature"
    )
    override_max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        le=4000,
        description="Override max_tokens"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "template_name": "summarization.text",
                "variables": {
                    "text": "Văn bản dài cần tóm tắt...",
                    "length": "3"
                },
                "provider": "openai"
            }
        }
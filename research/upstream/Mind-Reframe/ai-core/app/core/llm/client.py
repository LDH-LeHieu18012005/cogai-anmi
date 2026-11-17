from typing import Optional, Dict
from app.core.llm.base import BaseLLMProvider
from app.core.llm.providers.openai import OpenAIProvider
from app.core.llm.providers.groq import GroqProvider
from app.models.requests import LLMProvider
from app.utils.errors import InvalidProviderError, APIKeyError
from app.config import settings

class LLMClient:
    """
    Manager class để quản lý các LLM providers
    """
    
    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """
        Initialize các providers có sẵn API key
        """
        # OpenAI
        if settings.OPENAI_API_KEY:
            self._providers[LLMProvider.OPENAI.value] = OpenAIProvider(
                api_key=settings.OPENAI_API_KEY,
                default_model="gpt-4o-mini"
            )
        
        # Anthropic (sẽ implement ở bước sau)
        if settings.GROQ_API_KEY:
            self._providers[LLMProvider.GROQ.value] = GroqProvider(
                api_key=settings.GROQ_API_KEY, 
                base_url=settings.GROQ_BASE_URL,
                default_model="openai/gpt-oss-20b"
            )
    
    def get_provider(self, provider: LLMProvider) -> BaseLLMProvider:
        """
        Get provider instance
        
        Args:
            provider: LLMProvider enum
            
        Returns:
            BaseLLMProvider instance
            
        Raises:
            InvalidProviderError: Nếu provider không được support
            APIKeyError: Nếu API key chưa được config
        """
        provider_name = provider.value
        
        if provider_name not in self._providers:
            # Check xem có phải do missing API key không
            if provider == LLMProvider.OPENAI and not settings.OPENAI_API_KEY:
                raise APIKeyError("openai")
            elif provider == LLMProvider.GROQ and not settings.GROQ_API_KEY:
                raise APIKeyError("groq")
            else:
                raise InvalidProviderError(provider_name)
        
        return self._providers[provider_name]
    
    def list_available_providers(self) -> list[str]:
        """
        List các providers đã được initialize
        
        Returns:
            List provider names
        """
        return list(self._providers.keys())

# Singleton instance
llm_client = LLMClient()
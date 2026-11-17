from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, AsyncGenerator
from app.models.requests import Message

class BaseLLMProvider(ABC):
    def __init__(self, api_key: str, default_model: str):
        self.api_key=api_key
        self.default_model=default_model
        self._validate_api_key()
    def _validate_api_key(self):
        if not self.api_key:
            raise ValueError(f"API key is required for {self.__class__.__name__}")
        
    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 500,
        **kwargs
    ) -> Dict[str, Any]:
        pass

    def get_model(self, model: Optional[str] = None) -> str:
        return model if model else self.default_model
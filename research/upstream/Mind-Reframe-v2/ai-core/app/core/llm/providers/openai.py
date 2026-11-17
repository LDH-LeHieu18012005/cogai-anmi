from typing import Optional, List, Dict, Any, AsyncGenerator
from openai import AsyncOpenAI
from app.core.llm.base import BaseLLMProvider
from app.models.requests import Message, MessageRole
from app.utils.errors import LLMResponseError
import uuid

class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM Provider"""
    
    def __init__(self, api_key: str, default_model: str = "gpt-3.5-turbo"):
        super().__init__(api_key, default_model)
        self.client = AsyncOpenAI(api_key=api_key)
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """
        Convert từ Message objects sang format của OpenAI
        
        Args:
            messages: List Message objects
            
        Returns:
            List dict theo format OpenAI
        """
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]
    
    async def chat(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Thực hiện chat completion với OpenAI
        """
        try:
            model_name = self.get_model(model)
            openai_messages = self._convert_messages(messages)
            
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Extract response data
            message = response.choices[0].message
            usage = response.usage
            
            return {
                "id": response.id,
                "content": message.content,
                "model": response.model,
                "provider": "openai",
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                } if usage else None
            }
            
        except Exception as e:
            raise LLMResponseError(
                message=f"OpenAI API error: {str(e)}",
                detail=str(e)
            )
    
    async def chat_stream(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Thực hiện chat completion với streaming
        """
        try:
            model_name = self.get_model(model)
            openai_messages = self._convert_messages(messages)
            
            stream = await self.client.chat.completions.create(
                model=model_name,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise LLMResponseError(
                message=f"OpenAI streaming error: {str(e)}",
                detail=str(e)
            )
    
    async def completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 500,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Thực hiện text completion bằng cách convert sang chat format
        """
        # Tạo messages từ prompt
        messages = []
        
        if system_prompt:
            messages.append(
                Message(role=MessageRole.SYSTEM, content=system_prompt)
            )
        
        messages.append(
            Message(role=MessageRole.USER, content=prompt)
        )
        
        # Sử dụng chat method
        response = await self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Rename content thành text cho completion response
        return {
            "id": response["id"],
            "text": response["content"],
            "model": response["model"],
            "provider": response["provider"],
            "usage": response["usage"]
        }
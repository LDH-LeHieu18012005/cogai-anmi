from typing import List, Dict, Any, AsyncGenerator
from app.core.llm.client import llm_client
from app.core.cache.manager import cache_manager
from app.models.requests import ChatRequest, Message, LLMProvider
from app.models.responses import ChatResponse, Usage
from app.utils.errors import LLMResponseError
from app.utils.logger import logger
from app.config import settings

class ChatService:
    """
    Service layer cho chat functionality với caching
    """
    
    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """
        Xử lý chat request với caching
        
        Args:
            request: ChatRequest object
            
        Returns:
            ChatResponse object
        """
        try:
            # Generate cache key
            cache_key = cache_manager.generate_key(
                prefix="chat",
                provider=request.provider.value,
                model=request.model or "default",
                messages=[{"role": m.role.value, "content": m.content} for m in request.messages],
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            # Try to get from cache
            if settings.CACHE_ENABLED:
                cached_response = await cache_manager.get(cache_key)
                if cached_response:
                    logger.info(
                        f"Cache hit for chat request",
                        extra={"cache_key": cache_key[:16] + "..."}
                    )
                    return ChatResponse(**cached_response)
            
            logger.info(
                f"Processing chat request",
                extra={
                    "provider": request.provider.value,
                    "model": request.model,
                    "num_messages": len(request.messages),
                    "temperature": request.temperature,
                    "cache_key": cache_key[:16] + "..." if cache_key else None
                }
            )
            
            # Get provider
            provider = llm_client.get_provider(request.provider)
            
            # Call LLM
            response_data = await provider.chat(
                messages=request.messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            logger.info(
                f"Chat request completed successfully",
                extra={
                    "response_id": response_data["id"],
                    "model": response_data["model"],
                    "tokens_used": response_data.get("usage", {}).get("total_tokens", 0)
                }
            )
            
            # Convert to ChatResponse
            response = ChatResponse(
                id=response_data["id"],
                content=response_data["content"],
                model=response_data["model"],
                provider=response_data["provider"],
                usage=Usage(**response_data["usage"]) if response_data.get("usage") else None
            )
            
            # Cache the response
            if settings.CACHE_ENABLED and cache_key:
                await cache_manager.set(
                    cache_key,
                    response.model_dump(),
                    ttl=settings.CACHE_TTL
                )
                logger.debug(f"Response cached with key: {cache_key[:16]}...")
            
            return response
            
        except Exception as e:
            logger.error(
                f"Failed to process chat request: {str(e)}",
                exc_info=True
            )
            raise LLMResponseError(
                message=f"Failed to process chat: {str(e)}",
                detail=str(e)
            )
    
    async def process_chat_stream(
        self, 
        request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """
        Xử lý chat request với streaming response
        Streaming responses không được cache
        
        Args:
            request: ChatRequest object
            
        Yields:
            Các chunk text từ LLM
        """
        try:
            logger.info(
                f"Processing streaming chat request",
                extra={
                    "provider": request.provider.value,
                    "model": request.model,
                    "num_messages": len(request.messages)
                }
            )
            
            # Get provider
            provider = llm_client.get_provider(request.provider)
            
            # Stream response
            chunk_count = 0
            async for chunk in provider.chat_stream(
                messages=request.messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            ):
                chunk_count += 1
                yield chunk
            
            logger.info(
                f"Streaming chat completed",
                extra={"chunks_sent": chunk_count}
            )
                
        except Exception as e:
            logger.error(
                f"Failed to stream chat: {str(e)}",
                exc_info=True
            )
            raise LLMResponseError(
                message=f"Failed to stream chat: {str(e)}",
                detail=str(e)
            )

# Singleton instance
chat_service = ChatService()
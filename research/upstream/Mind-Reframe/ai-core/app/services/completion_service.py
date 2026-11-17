from typing import List, Dict, Any, AsyncGenerator
from app.core.llm.client import llm_client
from app.models.requests import CompletionRequest
from app.models.responses import CompletionResponse, Usage
from app.utils.errors import LLMResponseError

class CompletionService:
    async def process_completion(self, request: CompletionRequest) -> CompletionResponse:
        try:
            provider=llm_client.get_provider(request.provider)
            response_data=await provider.completion(
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            return CompletionResponse(
                id=response_data["id"],
                text=response_data["text"],
                model=response_data["model"],
                provider=response_data["provider"],
                usage=Usage(**response_data["usage"]) if response_data.get("usage") else None
            )
        except Exception as e:
            raise LLMResponseError(
                message=f"Failed to process chat: {str(e)}",
                detail=str(e)
            )

completion_service = CompletionService()
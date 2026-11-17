from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.requests import CompletionRequest
from app.models.responses import CompletionResponse, ErrorResponse
from app.services.completion_service import completion_service
from app.utils.errors import AIException

router = APIRouter()

@router.post(
    "/completion",
    response_model=CompletionResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Chat with LLM",
    description="Send conversation messages to LLM and receive response"
)

async def completion(request: CompletionRequest):
    try:
        response = await completion_service.process_completion(request)
        return response
    except AIException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from app.models.requests import ChatRequest
from app.models.responses import ChatResponse, ErrorResponse
from app.services.chat_service import chat_service
from app.utils.errors import AIException
from app.middleware.auth import optional_api_key  # hoặc verify_api_key nếu bắt buộc
from app.middleware.rate_limit import limiter

router = APIRouter()

@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Chat với LLM",
    description="Gửi conversation messages tới LLM và nhận response"
)
@limiter.limit("30/minute")  # Specific rate limit cho endpoint này
async def chat(
    request: Request,
    chat_request: ChatRequest,
    api_key: str = Depends(optional_api_key)  # Optional auth
):
    """
    Chat endpoint - gửi messages và nhận response từ LLM
    
    - **messages**: List các message trong conversation
    - **provider**: LLM provider (openai, anthropic)
    - **model**: Model cụ thể (optional)
    - **temperature**: Độ sáng tạo (0-2)
    - **max_tokens**: Số token tối đa
    """
    try:
        response = await chat_service.process_chat(chat_request)
        return response
        
    except AIException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/chat/stream",
    summary="Chat với streaming response",
    description="Gửi messages và nhận streaming response từ LLM"
)
@limiter.limit("20/minute")  # Lower limit cho streaming
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    api_key: str = Depends(optional_api_key)
):
    """
    Chat streaming endpoint - nhận response dạng stream
    
    Response sẽ được stream theo từng chunk text
    """
    try:
        async def generate():
            async for chunk in chat_service.process_chat_stream(chat_request):
                yield f"data: {chunk}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except AIException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
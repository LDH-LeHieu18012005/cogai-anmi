from fastapi import APIRouter
from app.models.responses import HealthResponse
from app.config import settings
from app.core.llm.client import llm_client

router = APIRouter()

@router.get(
    "/heath",
    response_model=HealthResponse,
    summary="Healh check",
    description="Check status of API and Providers"
)
async def health_check():
    available_providers = llm_client.list_available_providers()
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
    )

@router.get(
    "/providers",
    summary="List providers",
    description="Get list of LLM providers has been configured"
)
async def list_providers():
    return {
        "providers": llm_client.list_available_providers(),
        "total": len(llm_client.list_available_providers())
    }
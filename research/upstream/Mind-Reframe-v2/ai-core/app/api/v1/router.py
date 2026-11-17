from fastapi import APIRouter
from app.api.v1.endpoints import chat, completion, health, prompts, cache

api_router = APIRouter()

# Include các endpoint routers
api_router.include_router(
    chat.router,
    tags=["Chat"]
)

api_router.include_router(
    completion.router,
    tags=["Completion"]
)

api_router.include_router(
    prompts.router,
    prefix="/prompts",
    tags=["Prompts"]
)

api_router.include_router(
    cache.router,
    prefix="/cache",
    tags=["Cache"]
)

api_router.include_router(
    health.router,
    tags=["Health"]
)
from contextlib import asynccontextmanager
import httpx


@asynccontextmanager
async def provider_client(shared=None):
    if shared is not None:
        yield shared
    else:
        async with httpx.AsyncClient(timeout=40) as client:
            yield client

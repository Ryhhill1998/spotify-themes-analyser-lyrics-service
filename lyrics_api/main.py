import asyncio
from contextlib import asynccontextmanager
import httpx
import redis.asyncio as redis
from fastapi import FastAPI

from lyrics_api.services.storage_service import StorageService
from lyrics_api.settings import Settings
from lyrics_api.services.lyrics_scraper import LyricsScraper
from lyrics_api.routers import lyrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()

    semaphore = asyncio.Semaphore(settings.max_concurrent_scrapes)
    httpx_client = httpx.AsyncClient(base_url=settings.base_url, headers=settings.headers)

    redis_client = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)

    try:
        app.state.lyrics_scraper = LyricsScraper(semaphore=semaphore, client=httpx_client)
        app.state.storage_service = StorageService(redis_client)

        yield
    finally:
        await httpx_client.aclose()
        await redis_client.aclose()


app = FastAPI(lifespan=lifespan)

app.include_router(lyrics.router)

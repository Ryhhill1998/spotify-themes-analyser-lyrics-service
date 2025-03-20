import asyncio
from contextlib import asynccontextmanager

import aiosqlite
import httpx
from fastapi import FastAPI

from lyrics_api.services.storage.storage_service import initialise_db
from lyrics_api.settings import Settings
from lyrics_api.services.lyrics_scraper import LyricsScraper
from lyrics_api.routers import lyrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()

    # initialise database
    db = await aiosqlite.connect(settings.db_path)
    await initialise_db(db)
    await db.close()

    semaphore = asyncio.Semaphore(settings.max_concurrent_scrapes)
    httpx_client = httpx.AsyncClient(base_url=settings.base_url, headers=settings.headers)

    try:
        app.state.lyrics_scraper = LyricsScraper(semaphore=semaphore, client=httpx_client)

        yield
    finally:
        await httpx_client.aclose()


app = FastAPI(lifespan=lifespan)


# healthcheck route
@app.get("/")
def health_check():
    return {"status": "running"}


app.include_router(lyrics.router)

import asyncio
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import FastAPI, HTTPException, Depends

from lyrics_api.dependencies import get_data_service
from lyrics_api.models import LyricsResponse, LyricsRequest
from lyrics_api.services.data_service import DataService
from lyrics_api.settings import Settings
from lyrics_api.services.lyrics_scraper import LyricsScraper, LyricsScraperException


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    semaphore = asyncio.Semaphore(settings.max_concurrent_scrapes)
    client = httpx.AsyncClient(base_url=settings.base_url, headers=settings.headers)

    try:
        app.state.lyrics_scraper = LyricsScraper(semaphore=semaphore, client=client)
        yield
    finally:
        await client.aclose()


app = FastAPI(lifespan=lifespan)


@app.post('/lyrics-list')
async def get_lyrics(
        requested_lyrics: list[LyricsRequest],
        data_service: Annotated[DataService, Depends(get_data_service)]
) -> list[LyricsResponse]:
    try:
        lyrics_list = await data_service.get_lyrics_list(requested_lyrics)

        return lyrics_list
    except LyricsScraperException as e:
        raise HTTPException(status_code=404, detail="Lyrics not found.")

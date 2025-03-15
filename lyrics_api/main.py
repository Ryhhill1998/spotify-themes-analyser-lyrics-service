import asyncio
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Depends

from lyrics_api.dependencies import get_data_service
from lyrics_api.models import LyricsResponse, LyricsRequest
from lyrics_api.services.data_service import DataService, DataServiceException
from lyrics_api.services.storage_service import StorageService
from lyrics_api.settings import Settings
from lyrics_api.services.lyrics_scraper import LyricsScraper


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


@app.post("/lyrics", response_model=LyricsResponse)
async def get_lyrics(
        lyrics_request: LyricsRequest,
        data_service: Annotated[DataService, Depends(get_data_service)]
) -> LyricsResponse:
    try:
        lyrics = await data_service.get_lyrics(lyrics_request)
        print(f"LYRICS = {lyrics.model_dump()}")
        return lyrics
    except DataServiceException as e:
        print(e)
        raise HTTPException(status_code=404, detail="Lyrics not found.")


@app.get("/lyrics-test", response_model=LyricsResponse)
async def get_lyrics(
        artist_name: str,
        track_title: str,
        data_service: Annotated[DataService, Depends(get_data_service)]
) -> LyricsResponse:
    try:
        lyrics = await data_service.get_lyrics_test(artist_name=artist_name, track_title=track_title)
        return lyrics
    except DataServiceException as e:
        print(e)
        raise HTTPException(status_code=404, detail="Lyrics not found.")

import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException

from lyrics_service.settings import Settings
from lyrics_service.web_scraper import LyricsScraper, LyricsScraperException
from pydantic import BaseModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    semaphore = asyncio.Semaphore(settings.max_concurrent_scrapes)
    client = httpx.AsyncClient(timeout=5)
    app.state.lyrics_scraper = LyricsScraper(
        base_url=settings.base_url,
        headers=settings.headers,
        semaphore=semaphore,
        client=client
    )
    yield

    await client.aclose()


app = FastAPI(lifespan=lifespan)


class LyricsResponse(BaseModel):
    artist: str
    track_title: str
    lyrics: str


@app.get('/lyrics')
async def get_lyrics(artist: str, track_title: str) -> LyricsResponse:
    try:
        lyrics = await app.state.lyrics_scraper.scrape_lyrics(artist=artist, track_title=track_title)
        return LyricsResponse(artist=artist, track_title=track_title, lyrics=lyrics)
    except LyricsScraperException as e:
        raise HTTPException(status_code=404, detail="Lyrics not found.")

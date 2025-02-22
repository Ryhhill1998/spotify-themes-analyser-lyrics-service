from fastapi import FastAPI, HTTPException, Depends
from lyrics_service.web_scraper import WebScraper, WebScraperException
from pydantic import BaseModel
from typing import Annotated
from lyrics_service.settings import Settings
from lyrics_service.dependencies import get_settings

app = FastAPI()

class Lyrics(BaseModel):
    artist: str
    track_title: str
    lyrics: str

@app.get('/lyrics', response_model=Lyrics)
async def get_lyrics(artist: str, track_title: str, settings: Annotated[Settings, Depends(get_settings)]):

    try: 
        scraper = WebScraper(base_url=settings.base_url, headers=settings.headers)
        lyrics =scraper.scrape_lyrics(artist=artist, track_title=track_title)
        return Lyrics(artist=artist, track_title=track_title, lyrics=lyrics)
    
    except WebScraperException as e:
        raise HTTPException(status_code=404, detail=str(e))
import asyncio
import uuid

from lyrics_api.models import LyricsResponse, LyricsRequest
from lyrics_api.services.lyrics_scraper import LyricsScraper, LyricsScraperException
from lyrics_api.services.storage_service import StorageService


class DataService:
    def __init__(self, lyrics_scraper: LyricsScraper, storage_service: StorageService):
        self.lyrics_scraper = lyrics_scraper
        self.storage_service = storage_service

    async def get_lyrics(self, lyrics_request: LyricsRequest) -> LyricsResponse:
        track_id = lyrics_request.track_id
        artist_name = lyrics_request.artist_name
        track_title = lyrics_request.track_title

        lyrics = await self.storage_service.retrieve_item(track_id)

        if lyrics is None:
            lyrics = await self.lyrics_scraper.scrape_lyrics(artist_name=artist_name, track_title=track_title)
            await self.storage_service.store_item(key=track_id, value=lyrics)

        lyrics_response = LyricsResponse(track_id=track_id, artist_name=artist_name, track_title=track_title, lyrics=lyrics)

        return lyrics_response

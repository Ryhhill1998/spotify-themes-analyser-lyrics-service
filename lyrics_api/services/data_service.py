import asyncio

from lyrics_api.models import LyricsResponse, LyricsRequest
from lyrics_api.services.lyrics_scraper import LyricsScraper
from lyrics_api.services.storage_service import StorageService


class DataService:
    def __init__(self, lyrics_scraper: LyricsScraper, storage_service: StorageService):
        self.lyrics_scraper = lyrics_scraper
        self.storage_service = storage_service

    @staticmethod
    def _create_lyrics_response(artist: str, track_title: str, lyrics: str) -> LyricsResponse:
        return LyricsResponse(artist=artist, track_title=track_title, lyrics=lyrics)

    async def get_lyrics(self, artist: str, track_title: str) -> LyricsResponse:
        lyrics = await self.lyrics_scraper.scrape_lyrics(artist=artist, track_title=track_title)

        lyrics_response = self._create_lyrics_response(artist=artist, track_title=track_title, lyrics=lyrics)

        return lyrics_response

    async def get_lyrics_list(self, requested_lyrics: list[LyricsRequest]) -> list[LyricsResponse]:
        tasks = []

        for req in requested_lyrics:
            coroutine = self.get_lyrics(artist=req.artist, track_title=req.track_title)
            tasks.append(coroutine)

        lyrics_list = await asyncio.gather(*tasks)

        return lyrics_list

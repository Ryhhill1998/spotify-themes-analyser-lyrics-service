import asyncio

from lyrics_api.models import LyricsResponse, LyricsRequest
from lyrics_api.services.lyrics_scraper import LyricsScraper
from lyrics_api.services.storage_service import StorageService


class DataService:
    def __init__(self, lyrics_scraper: LyricsScraper, storage_service: StorageService):
        self.lyrics_scraper = lyrics_scraper
        self.storage_service = storage_service

    async def _get_lyrics(self, track_id: str, artist_name: str, track_title: str) -> LyricsResponse:
        lyrics = None

        try:
            lyrics = await self.storage_service.retrieve_item(track_id)

            if lyrics is None:
                lyrics = await self.lyrics_scraper.scrape_lyrics(artist_name=artist_name, track_title=track_title)
                await self.storage_service.store_item(key=track_id, value=lyrics)
        except Exception as e:
            print(e)

        lyrics_response = LyricsResponse(
            track_id=track_id,
            artist_name=artist_name,
            track_title=track_title,
            lyrics=lyrics
        )

        return lyrics_response

    async def get_lyrics_list(self, requested_lyrics: list[LyricsRequest]) -> list[LyricsResponse]:
        tasks = [
            self._get_lyrics(
                track_id=req.track_id,
                artist_name=req.artist_name,
                track_title=req.track_title
            )
            for req
            in requested_lyrics
        ]

        lyrics_list = await asyncio.gather(*tasks, return_exceptions=True)

        return lyrics_list

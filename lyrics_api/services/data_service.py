import asyncio

from lyrics_api.models import LyricsResponse, LyricsRequest
from lyrics_api.services.lyrics_scraper import LyricsScraper
from lyrics_api.services.storage_service import StorageService


class DataService:
    def __init__(self, lyrics_scraper: LyricsScraper, storage_service: StorageService):
        self.lyrics_scraper = lyrics_scraper
        self.storage_service = storage_service

    async def _get_lyrics_from_storage(self, track_id: str) -> str:
        stored_lyrics = await self.storage_service.retrieve_item(track_id)

        return stored_lyrics

    async def _get_lyrics(self, track_id: str, artist_name: str, track_title: str) -> LyricsResponse:
        lyrics = await self.storage_service.retrieve_item(track_id)

        if lyrics is None:
            lyrics = await self.lyrics_scraper.scrape_lyrics(artist_name=artist_name, track_title=track_title)
            await self.storage_service.store_item(key=track_id, value=lyrics)

        lyrics_response = LyricsResponse(id=track_id, artist_name=artist_name, track_title=track_title, lyrics=lyrics)

        return lyrics_response

    async def get_lyrics_list(self, requested_lyrics: list[LyricsRequest]) -> list[LyricsResponse]:
        tasks = []

        for req in requested_lyrics:
            coroutine = self._get_lyrics(track_id=req.id, artist_name=req.artist_name, track_title=req.track_title)
            tasks.append(coroutine)

        lyrics_list = await asyncio.gather(*tasks, return_exceptions=True)

        successful_results = [item for item in lyrics_list if not isinstance(item, Exception)]
        failed_count = len(lyrics_list) - len(successful_results)
        print(f"Success: {len(successful_results)}")

        # Ensure at least 50% success rate
        if len(successful_results) >= len(lyrics_list) // 2:
            return successful_results
        else:
            raise RuntimeError(f"Too many failures! Only {len(successful_results)} succeeded, {failed_count} failed.")

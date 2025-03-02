from typing import Annotated
from fastapi import Depends, Request

from lyrics_api.services.data_service import DataService
from lyrics_api.services.lyrics_scraper import LyricsScraper
from lyrics_api.services.storage_service import StorageService


def get_lyrics_scraper(request: Request) -> LyricsScraper:
    return request.app.state.lyrics_scraper


def get_storage_service() -> StorageService:
    return StorageService()


def get_data_service(
        lyrics_scraper: Annotated[LyricsScraper, Depends(get_lyrics_scraper)],
        storage_service: Annotated[StorageService, Depends(get_storage_service)]
) -> DataService:
    return DataService(lyrics_scraper=lyrics_scraper, storage_service=storage_service)

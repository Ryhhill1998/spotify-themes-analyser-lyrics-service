from lyrics_service.settings import Settings
from functools import lru_cache
from lyrics_service.web_scraper import LyricsScraper
from typing import Annotated
from fastapi import Depends


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_lyrics_scraper(settings: Annotated[Settings, Depends(get_settings)]) -> LyricsScraper:
    return LyricsScraper(base_url=settings.base_url, headers=settings.headers)

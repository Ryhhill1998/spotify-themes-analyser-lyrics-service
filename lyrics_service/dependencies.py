from lyrics_service.settings import Settings
from functools import lru_cache


@lru_cache
def get_settings() -> Settings:
    return Settings()

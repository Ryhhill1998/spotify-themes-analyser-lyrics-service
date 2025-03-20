from functools import lru_cache
from typing import Annotated

import aiosqlite
from fastapi import Depends, Request

from lyrics_api.services.data_service import DataService
from lyrics_api.services.lyrics_scraper import LyricsScraper
from lyrics_api.services.storage.storage_service import StorageService
from lyrics_api.settings import Settings


@lru_cache
def get_settings() -> Settings:
    """
    Retrieves the application settings.

    The settings are cached to optimize performance, ensuring they are only loaded once per application instance.

    Returns
    -------
    Settings
        The application settings instance.
    """

    return Settings()


SettingsDependency = Annotated[Settings, Depends(get_settings)]


def get_lyrics_scraper(request: Request) -> LyricsScraper:
    """
    Retrieves the LyricsScraper instance from the FastAPI application state.

    Parameters
    ----------
    request : Request
        The FastAPI request object.

    Returns
    -------
    LyricsScraper
        The lyrics scraper instance stored in the application state.
    """

    return request.app.state.lyrics_scraper


async def get_db_conn(settings: SettingsDependency):
    """Dependency to get an async database connection."""
    db = await aiosqlite.connect(settings.db_path)

    try:
        yield db  # Provide connection to route handlers
    finally:
        await db.close()


DBConnectionDependency = Annotated[aiosqlite.Connection, Depends(get_db_conn)]


def get_storage_service(db_conn: DBConnectionDependency) -> StorageService:
    """
    Retrieves the storage service from the FastAPI application state.

    Parameters
    ----------
    db_conn : DBConnectionDependency
        The connection to the database.

    Returns
    -------
    StorageService
        The configured StorageService instance.
    """

    return StorageService(db_conn)


def get_data_service(
        lyrics_scraper: Annotated[LyricsScraper, Depends(get_lyrics_scraper)],
        storage_service: Annotated[StorageService, Depends(get_storage_service)]
) -> DataService:
    """
    Creates a DataService instance using the provided LyricsScraper and StorageService.

    Parameters
    ----------
    lyrics_scraper : LyricsScraper
        The lyrics scraper dependency.
    storage_service : StorageService
        The storage service dependency.

    Returns
    -------
    DataService
        An instance of DataService configured with the given dependencies.
    """

    return DataService(lyrics_scraper=lyrics_scraper, storage_service=storage_service)


DataServiceDependency = Annotated[DataService, Depends(get_data_service)]
"""
Annotated dependency for injecting a DataService instance in FastAPI routes.
"""


from typing import Annotated
from fastapi import Depends, Request

from lyrics_api.services.data_service import DataService
from lyrics_api.services.lyrics_scraper import LyricsScraper
from lyrics_api.services.storage_service import StorageService


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


def get_storage_service(request: Request) -> StorageService:
    """
    Retrieves the StorageService instance from the FastAPI application state.

    Parameters
    ----------
    request : Request
        The FastAPI request object.

    Returns
    -------
    StorageService
        The storage service instance stored in the application state.
    """

    return request.app.state.storage_service


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


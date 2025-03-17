import pydantic

from lyrics_api.models import LyricsResponse, LyricsRequest
from lyrics_api.services.lyrics_scraper import LyricsScraper, LyricsScraperException, LyricsScraperNotFoundException
from lyrics_api.services.storage_service import StorageService, StorageServiceException


class DataServiceException(Exception):
    """Base exception for errors encountered in the DataService."""

    def __init__(self, message: str):
        super().__init__(message)


class DataServiceNotFoundException(DataServiceException):
    """
    Exception raised when lyrics cannot be found.

    This exception is triggered when lyrics are not found either in the storage service or via web scraping.
    """

    def __init__(self, message: str):
        super().__init__(message)


class DataService:
    """
    Handles the retrieval and storage of song lyrics.

    This service first attempts to retrieve lyrics from a storage backend. If the lyrics are not found, it falls back
    to scraping them from an external source. Once obtained, the lyrics are stored for future use.

    Attributes
    ----------
    lyrics_scraper : LyricsScraper
        The scraper service used to fetch lyrics from the web.
    storage_service : StorageService
        The storage service used to persist lyrics.

    Methods
    -------
    get_lyrics(lyrics_request: LyricsRequest) -> LyricsResponse
        Retrieves lyrics and returns them in a structured response format.
    """

    def __init__(self, lyrics_scraper: LyricsScraper, storage_service: StorageService):
        """
        Initializes the DataService with a lyrics scraper and a storage service.

        Parameters
        ----------
        lyrics_scraper : LyricsScraper
            The scraper service used to fetch lyrics from the web.
        storage_service : StorageService
            The storage service used to persist lyrics.
        """

        self.lyrics_scraper = lyrics_scraper
        self.storage_service = storage_service

    async def _get_lyrics(self, track_id: str, artist_name: str, track_title: str) -> str:
        """
        Retrieves lyrics from storage or scrapes them if not found.

        If the lyrics exist in the storage service, they are returned immediately. Otherwise, they are scraped from an
        external source and stored for future use.

        Parameters
        ----------
        track_id : str
            The unique identifier of the track.
        artist_name : str
            The name of the artist.
        track_title : str
            The title of the song.

        Returns
        -------
        str
            The retrieved lyrics.

        Raises
        ------
        LyricsScraperNotFoundException
            If lyrics cannot be found via web scraping.
        LyricsScraperException
            If another error occurs while scraping lyrics.
        StorageServiceException
            If an error occurs while storing or retrieving lyrics via the storage service.
        """

        lyrics = await self.storage_service.retrieve_item(track_id)

        if lyrics is None:
            lyrics = await self.lyrics_scraper.scrape_lyrics(artist_name=artist_name, track_title=track_title)
            await self.storage_service.store_item(key=track_id, value=lyrics)

        return lyrics

    async def get_lyrics(self, lyrics_request: LyricsRequest) -> LyricsResponse:
        """
        Retrieves lyrics based on a request.

        This method attempts to get lyrics using `_get_lyrics()`, handling any exceptions that may occur and returning
        structured error responses.

        Parameters
        ----------
        lyrics_request : LyricsRequest
            The request object containing track ID, artist name, and track title.

        Returns
        -------
        LyricsResponse
            A structured response containing the lyrics and metadata.

        Raises
        ------
        DataServiceNotFoundException
            If the lyrics cannot be found while scraping.
        DataServiceException
            If there is a different issue with retrieving or storing the lyrics.
        """

        track_id = lyrics_request.track_id
        artist_name = lyrics_request.artist_name
        track_title = lyrics_request.track_title

        try:
            lyrics = await self._get_lyrics(track_id=track_id, artist_name=artist_name, track_title=track_title)

            lyrics_response = LyricsResponse(
                track_id=track_id,
                artist_name=artist_name,
                track_title=track_title,
                lyrics=lyrics
            )

            return lyrics_response
        except LyricsScraperNotFoundException as e:
            message = (
                f"Lyrics not found for track_id: {track_id}, artist_name: {artist_name}, track_title: {track_title}"
                f" - {e}"
            )
            print(message)
            raise DataServiceNotFoundException(message)
        except (LyricsScraperException, StorageServiceException) as e:
            message = (
                f"Failed to retrieve lyrics for track_id: {track_id}, artist_name: {artist_name}, "
                f"track_title: {track_title} - {e}"
            )
            print(message)
            raise DataServiceException(message)
        except pydantic.ValidationError as e:
            message = f"Failed to create LyricsResponse object - {e}"
            print(message)
            raise DataServiceException(message)

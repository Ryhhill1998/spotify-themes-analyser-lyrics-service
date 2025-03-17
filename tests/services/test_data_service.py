from unittest.mock import AsyncMock

import pytest

from lyrics_api.models import LyricsRequest, LyricsResponse
from lyrics_api.services.data_service import DataService, DataServiceException
from lyrics_api.services.lyrics_scraper import LyricsScraper, LyricsScraperNotFoundException, LyricsScraperException
from lyrics_api.services.storage_service import StorageService, StorageServiceException


@pytest.fixture
def mock_lyrics_scraper() -> AsyncMock:
    return AsyncMock(spec=LyricsScraper)


@pytest.fixture
def mock_storage_service() -> AsyncMock:
    return AsyncMock(spec=StorageService)


@pytest.fixture
def data_service(mock_lyrics_scraper, mock_storage_service) -> DataService:
    return DataService(lyrics_scraper=mock_lyrics_scraper, storage_service=mock_storage_service)


@pytest.fixture
def mock_lyrics_request() -> LyricsRequest:
    return LyricsRequest(track_id="1", artist_name="Artist 1", track_title="Track 1")


# 1. Test _get_lyrics calls lyrics_scraper.scrape_lyrics if lyrics not in storage service.
@pytest.mark.asyncio
async def test__get_lyrics_lyrics_not_stored(data_service, mock_lyrics_scraper, mock_storage_service):
    mock_retrieve_item = AsyncMock()
    mock_retrieve_item.return_value = None
    mock_storage_service.retrieve_item = mock_retrieve_item
    lyrics = "Lyrics for track 1"
    mock_scrape_lyrics = AsyncMock()
    mock_scrape_lyrics.return_value = lyrics
    mock_lyrics_scraper.scrape_lyrics = mock_scrape_lyrics
    track_id = "1"
    artist_name = "Artist 1"
    track_title = "Track 1"

    await data_service._get_lyrics(track_id=track_id, artist_name=artist_name, track_title=track_title)

    mock_lyrics_scraper.scrape_lyrics.assert_called_once_with(artist_name=artist_name, track_title=track_title)
    mock_storage_service.store_item.assert_called_once_with(key=track_id, value=lyrics)


# 2. Test _get_lyrics does not call lyrics_scraper.scrape_lyrics if lyrics in storage service.
@pytest.mark.asyncio
async def test__get_lyrics_lyrics_are_stored(data_service, mock_lyrics_scraper, mock_storage_service):
    mock_retrieve_item = AsyncMock()
    lyrics =  "Lyrics for track 1"
    mock_retrieve_item.return_value = lyrics
    mock_storage_service.retrieve_item = mock_retrieve_item
    track_id = "1"
    artist_name = "Artist 1"
    track_title = "Track 1"

    found_lyrics = await data_service._get_lyrics(track_id=track_id, artist_name=artist_name, track_title=track_title)

    mock_lyrics_scraper.scrape_lyrics.assert_not_called()
    assert found_lyrics == lyrics


# 3. Test get_lyrics raises DataServiceException if _get_lyrics raises LyricsScraperNotFoundException.
@pytest.mark.asyncio
async def test_get_lyrics_lyrics_scraper_not_found_exception(data_service, mock_lyrics_request):
    mock__get_lyrics = AsyncMock()
    mock__get_lyrics.side_effect = LyricsScraperNotFoundException("Test")
    data_service._get_lyrics = mock__get_lyrics

    with pytest.raises(
            DataServiceException,
            match=f"Lyrics not found for track_id: {mock_lyrics_request.track_id}, "
                  f"artist_name: {mock_lyrics_request.artist_name}, "
                  f"track_title: {mock_lyrics_request.track_title}"
    ):
        await data_service.get_lyrics(mock_lyrics_request)


# 4. Test get_lyrics raises DataServiceException if _get_lyrics raises StorageServiceException.
@pytest.mark.asyncio
async def test_get_lyrics_storage_service_exception(data_service, mock_lyrics_request):
    mock__get_lyrics = AsyncMock()
    mock__get_lyrics.side_effect = StorageServiceException("Test")
    data_service._get_lyrics = mock__get_lyrics

    with pytest.raises(
            DataServiceException,
            match=f"Failed to retrieve lyrics for track_id: {mock_lyrics_request.track_id}, "
                  f"artist_name: {mock_lyrics_request.artist_name}, "
                  f"track_title: {mock_lyrics_request.track_title}"
    ):
        await data_service.get_lyrics(mock_lyrics_request)


# 5. Test get_lyrics raises DataServiceException if _get_lyrics raises LyricsServiceException.
@pytest.mark.asyncio
async def test_get_lyrics_lyrics_scraper_exception(data_service, mock_lyrics_request):
    mock__get_lyrics = AsyncMock()
    mock__get_lyrics.side_effect = LyricsScraperException("Test")
    data_service._get_lyrics = mock__get_lyrics

    with pytest.raises(
            DataServiceException,
            match=f"Failed to retrieve lyrics for track_id: {mock_lyrics_request.track_id}, "
                  f"artist_name: {mock_lyrics_request.artist_name}, "
                  f"track_title: {mock_lyrics_request.track_title}"
    ):
        await data_service.get_lyrics(mock_lyrics_request)


# 6. Test get_lyrics raises DataServiceException if lyrics validation fails.
@pytest.mark.asyncio
async def test_get_lyrics_data_validation_failure(data_service, mock_lyrics_request):
    mock__get_lyrics = AsyncMock()
    mock__get_lyrics.return_value = None
    data_service._get_lyrics = mock__get_lyrics

    with pytest.raises(DataServiceException, match="Failed to create LyricsResponse object"):
        await data_service.get_lyrics(mock_lyrics_request)


# 7. Test get_lyrics returns expected lyrics response.
@pytest.mark.asyncio
async def test_get_lyrics_success(data_service, mock_lyrics_request):
    lyrics = "Lyrics for track 1"
    mock__get_lyrics = AsyncMock()
    mock__get_lyrics.return_value = lyrics
    data_service._get_lyrics = mock__get_lyrics

    lyrics_response = await data_service.get_lyrics(mock_lyrics_request)

    assert lyrics_response == LyricsResponse(
        track_id=mock_lyrics_request.track_id,
        artist_name=mock_lyrics_request.artist_name,
        track_title=mock_lyrics_request.track_title,
        lyrics=lyrics
    )

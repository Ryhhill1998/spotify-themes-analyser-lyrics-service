from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from lyrics_api.dependencies import get_data_service
from lyrics_api.main import app
from lyrics_api.models import LyricsRequest, LyricsResponse
from lyrics_api.services.data_service import DataService, DataServiceNotFoundException, DataServiceException


# 1. Test /lyrics returns a 404 status code the data service raises a DataServiceNotFoundException exception.
# 2. Test /lyrics returns a 500 status code if the data service raises any other exception.
# 3. Test /lyrics returns expected response if successful.


@pytest.fixture
def mock_data_service() -> Mock:
    return Mock(spec=DataService)


@pytest.fixture
def client(mock_data_service) -> TestClient:
    app.dependency_overrides[get_data_service] = lambda: mock_data_service
    return TestClient(app)


@pytest.fixture
def mock_lyrics_request() -> dict[str, str]:
    return {
        "track_id": "1",
        "artist_name": "Artist 1",
        "track_title": "Track 1"
    }


def test_lyrics_data_service_not_found_exception(client, mock_data_service, mock_lyrics_request):
    mock_get_lyrics = AsyncMock()
    mock_get_lyrics.side_effect = DataServiceNotFoundException("Test")
    mock_data_service.get_lyrics = mock_get_lyrics

    res = client.post("/lyrics", json=mock_lyrics_request)

    assert res.status_code == 404 and res.json() == {"detail": "Lyrics not found."}


def test_lyrics_data_service_exception(client, mock_data_service, mock_lyrics_request):
    mock_get_lyrics = AsyncMock()
    mock_get_lyrics.side_effect = DataServiceException("Test")
    mock_data_service.get_lyrics = mock_get_lyrics

    res = client.post("/lyrics", json=mock_lyrics_request)

    assert res.status_code == 500 and res.json() == {"detail": "Something went wrong."}


def test_lyrics_general_exception(client, mock_data_service, mock_lyrics_request):
    mock_get_lyrics = AsyncMock()
    mock_get_lyrics.side_effect = Exception("Test")
    mock_data_service.get_lyrics = mock_get_lyrics

    res = client.post("/lyrics", json=mock_lyrics_request)

    assert res.status_code == 500 and res.json() == {"detail": "Something went wrong."}


def test_lyrics_success(client, mock_data_service, mock_lyrics_request):
    mock_get_lyrics = AsyncMock()
    mock_get_lyrics.return_value = LyricsResponse(
        track_id="1",
        artist_name="Artist 1",
        track_title="Track 1",
        lyrics="Lyrics for track 1"
    )
    mock_data_service.get_lyrics = mock_get_lyrics

    res = client.post("/lyrics", json=mock_lyrics_request)

    assert res.status_code == 200 and res.json() == {
        "track_id": "1",
        "artist_name": "Artist 1",
        "track_title": "Track 1",
        "lyrics": "Lyrics for track 1"
    }

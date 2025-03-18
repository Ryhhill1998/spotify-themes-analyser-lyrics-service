from fastapi import APIRouter, HTTPException

from lyrics_api.dependencies import DataServiceDependency
from lyrics_api.models import LyricsResponse, LyricsRequest
from lyrics_api.services.data_service import DataServiceNotFoundException, DataServiceException

router = APIRouter()


@router.post("/lyrics", response_model=LyricsResponse)
async def get_lyrics(lyrics_request: LyricsRequest, data_service: DataServiceDependency) -> LyricsResponse:
    """
    Retrieves song lyrics based on the given request.

    This endpoint fetches lyrics using the provided `DataServiceDependency` which manages the retrieval and storage of
    lyrics.

    Parameters
    ----------
    lyrics_request : LyricsRequest
        The request object containing track ID, artist name, and track title.
    data_service : DataServiceDependency
        The data service dependency responsible for retrieving and storing lyrics.

    Returns
    -------
    LyricsResponse
        A structured response containing the track ID, artist name, track title, and lyrics.

    Raises
    ------
    HTTPException
        - 404 : If the lyrics cannot be found.
        - 500 : If an unexpected error occurs during retrieval.
    """

    try:
        lyrics = await data_service.get_lyrics(lyrics_request)
        return lyrics
    except DataServiceNotFoundException as e:
        print(e)
        raise HTTPException(status_code=404, detail="Lyrics not found.")
    except DataServiceException as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something went wrong.")

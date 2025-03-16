from fastapi import APIRouter, HTTPException

from lyrics_api.dependencies import DataServiceDependency
from lyrics_api.models import LyricsResponse, LyricsRequest
from lyrics_api.services.data_service import DataServiceException

router = APIRouter()


@router.post("/lyrics", response_model=LyricsResponse)
async def get_lyrics(lyrics_request: LyricsRequest, data_service: DataServiceDependency) -> LyricsResponse:
    try:
        lyrics = await data_service.get_lyrics(lyrics_request)
        return lyrics
    except DataServiceException as e:
        print(e)
        raise HTTPException(status_code=404, detail="Lyrics not found.")

from pydantic import BaseModel


class LyricsRequest(BaseModel):
    track_id: str
    artist_name: str
    track_title: str


class LyricsResponse(LyricsRequest):
    lyrics: str

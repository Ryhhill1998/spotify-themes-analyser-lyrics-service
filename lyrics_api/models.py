from pydantic import BaseModel


class LyricsRequest(BaseModel):
    artist: str
    track_title: str


class LyricsResponse(LyricsRequest):
    lyrics: str

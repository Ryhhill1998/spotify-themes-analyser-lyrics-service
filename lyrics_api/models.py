from pydantic import BaseModel


class LyricsRequest(BaseModel):
    """
    Data model for a lyrics request.

    Attributes
    ----------
    track_id : str
        Unique identifier for the track.
    artist_name : str
        Name of the artist.
    track_title : str
        Title of the track.
    """

    track_id: str
    artist_name: str
    track_title: str


class LyricsResponse(LyricsRequest):
    """
    Data model for a lyrics response.

    Inherits from LyricsRequest which provides the track_id, artist_name and track_title.

    Attributes
    ----------
    lyrics : str
        The lyrics of the requested track.
    """

    lyrics: str

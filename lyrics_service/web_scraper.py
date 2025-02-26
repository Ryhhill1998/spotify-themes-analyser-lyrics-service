import requests
from bs4 import BeautifulSoup


class LyricsScraperException(Exception):

    def __init__(self, message: str ):
        super().__init__(message)


class LyricsScraper:

    def __init__(self, base_url: str, headers : dict[str,str]):

        self.base_url = base_url
        self.headers = headers

    def _get_html(self, url: str) -> str:

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.text

    def _get_url(self, artist: str, title: str) -> str:

        def format_string(string: str):
            return string.lower().replace(" ", "-")

        artist = format_string(artist)
        title = format_string(title)
        url=f"{self.base_url}/{artist}-{title}-lyrics"

        return url

    def scrape_lyrics(self, artist: str, track_title: str) -> str:
        
        try:
            url = self._get_url(artist, track_title)
            html = self._get_html(url)
            soup = BeautifulSoup(html, "html.parser")
            lyrics_container = soup.select("div[data-lyrics-container='true']")
            
            if lyrics_container:
                lyrics = " ".join([container.get_text(separator=" ").strip() for container in lyrics_container])

            else:
                raise LyricsScraperException("Lyrics not found!")
            return lyrics

        except Exception: 
        
            raise LyricsScraperException(f"An error occurred while scraping the lyrics")
        
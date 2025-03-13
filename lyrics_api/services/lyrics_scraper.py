import asyncio
import random
import string
import httpx
import re
from bs4 import BeautifulSoup


class LyricsScraperException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class LyricsScraper:
    def __init__(self, semaphore: asyncio.Semaphore, client: httpx.AsyncClient):
        self.semaphore = semaphore
        self.client = client

    @staticmethod
    def _get_url(artist: str, title: str) -> str:
        def format_string(strings: str):
            strings = re.sub(r"(\s*\(feat.*?\)\s*|\s*feat.*\s*)", "", strings)
            strings = strings.replace("$", "-").replace("&", "and")
            chars_to_remove = "-'`"
            punc = ''.join(c for c in string.punctuation if c not in chars_to_remove)
            strings = strings.translate(str.maketrans("", "", punc))
            return strings.lower().replace(" ", "-")

        artist = format_string(artist)
        artist = artist[0].upper() + artist[1:]
        title = format_string(title)
        url = f"/{artist}-{title}-lyrics"

        return url

    async def _get_html(self, url: str) -> str:
        async with self.semaphore:
            await asyncio.sleep(random.uniform(0.25, 1))
            response = await self.client.get(url=url, follow_redirects=True)

        response.raise_for_status()

        return response.text

    async def scrape_lyrics(self, artist_name: str, track_title: str) -> str:
        try:
            url = self._get_url(artist_name, track_title)
            html = await self._get_html(url)
            soup = BeautifulSoup(html, "html.parser")

            lyrics_containers = soup.select("div[data-lyrics-container='true']")

            if not lyrics_containers:
                raise LyricsScraperException("Lyrics not found!")

            lyrics = "\n".join([container.get_text(separator=" ").strip() for container in lyrics_containers])
            print(f"Success: {url}")
            return lyrics
        except Exception as e:
            print(f"Failure: {url}")
            print(e)
            raise LyricsScraperException(f"An error occurred while scraping the lyrics")

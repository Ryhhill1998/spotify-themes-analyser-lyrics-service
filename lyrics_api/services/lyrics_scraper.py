import asyncio
import random
import string
import unicodedata

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
        def format_string(s: str) -> str:
            """Formats artist_name and track_title strings into appropriate url format"""

            # Normalize Unicode characters
            s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')

            def handle_parentheses(match):
                """Removes content if it contains 'feat' or 'with'"""

                content = match.group(1).lower()
                return "" if "feat" in content or "with" in content else content

            s = re.sub(r"\(([^)]*)\)", handle_parentheses, s)

            # Remove ' - feat' and 'feat'
            s = re.sub(r"\s*-\s*feat.*", "", s, flags=re.IGNORECASE)
            s = re.sub(r"\s*feat.*", "", s, flags=re.IGNORECASE)

            # Replace special characters and punctuation
            s = s.replace("$", "-").replace("&", "and")
            s = s.translate(str.maketrans("", "", string.punctuation.replace("-", "")))

            # Convert to lowercase, replace hyphens with '-' and remove leading/trailing '-'
            s = s.lower().replace(" ", "-").strip("-")

            s = re.sub(r'-+', '-', s)

            return s

        artist = format_string(artist)
        artist = artist[0].upper() + artist[1:] if artist else ""
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

            lyrics = ""

            for container in lyrics_containers:
                inner_html = "".join(str(item) for item in container.contents)
                lyrics += inner_html + "<br/><br/>"

            print(f"Success: {url}")
            return lyrics
        except Exception as e:
            print(f"Failure: {url}")
            print(e)
            raise LyricsScraperException(f"An error occurred while scraping the lyrics")

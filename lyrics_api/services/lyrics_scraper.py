import asyncio
import random
import string
import unicodedata

import httpx
import re
from bs4 import BeautifulSoup, Tag


class LyricsScraperException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class LyricsScraper:
    """
    A scraper for fetching song lyrics from a specified website.

    Attributes
    ----------
    semaphore : asyncio.Semaphore
        An asyncio semaphore to limit concurrent requests.
    client : httpx.AsyncClient
        An asynchronous HTTP client for making requests.

    Methods
    -------
    scrape_lyrics(artist_name: str, track_title: str) -> str
        Asynchronously scrapes the lyrics for a given artist and song title.
    """

    def __init__(self, semaphore: asyncio.Semaphore, client: httpx.AsyncClient):
        """
        Parameters
        ----------
        semaphore : asyncio.Semaphore
            Semaphore to manage concurrent requests.
        client : httpx.AsyncClient
            Asynchronous HTTP client for making web requests.
        """

        self.semaphore = semaphore
        self.client = client

    @staticmethod
    def _get_url(artist: str, title: str) -> str:
        """
        Generates a formatted URL for retrieving lyrics based on the artist and song title.

        Parameters
        ----------
        artist : str
            The name of the artist.
        title : str
            The title of the song.

        Returns
        -------
        str
            The formatted URL path for fetching lyrics.

        Raises
        ------
        LyricsScraperException
            If Unicode normalisation of input string fails.
        """

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

        try:
            artist = format_string(artist)
            artist = artist[0].upper() + artist[1:] if artist else ""
            title = format_string(title)
            url = f"/{artist}-{title}-lyrics"

            return url
        except UnicodeError as e:
            message = f"Failed to decode character - {e}"
            print(message)
            raise LyricsScraperException(message)

    async def _get_html(self, url: str) -> str:
        """
        Fetches the HTML content from the given URL asynchronously.

        Parameters
        ----------
        url : str
            The URL to fetch HTML content from.

        Returns
        -------
        str
            The raw HTML content of the page.

        Raises
        ------
        LyricsScraperException
            If the request fails or the response cannot be decoded.
        """

        try:
            async with self.semaphore:
                await asyncio.sleep(random.uniform(0.25, 1))
                response = await self.client.get(url=url, follow_redirects=True)

            response.raise_for_status()

            return response.text
        except httpx.InvalidURL as e:
            message = f"Invalid URL - {e}"
            print(message)
            raise LyricsScraperException(message)
        except httpx.TimeoutException as e:
            message = f"Request timed out - {e}"
            print(message)
            raise LyricsScraperException(message)
        except httpx.RequestError as e:
            message = f"Request failed - {e}"
            print(message)
            raise LyricsScraperException(message)
        except httpx.HTTPStatusError as e:
            message = f"Non-2XX status code - {e}"
            print(message)
            raise LyricsScraperException(message)
        except UnicodeDecodeError as e:
            message = f"Failed to decode response - {e}"
            print(message)
            raise LyricsScraperException(message)

    async def scrape_lyrics(self, artist_name: str, track_title: str) -> str:
        """
        Asynchronously scrapes the lyrics for a given artist and song title.

        Parameters
        ----------
        artist_name : str
            The name of the artist.
        track_title : str
            The title of the song.

        Returns
        -------
        str
            The scraped lyrics as an HTML-formatted string.

        Raises
        ------
        LyricsScraperException
            If an error occurs while scraping the lyrics.
        """

        try:
            url = self._get_url(artist_name, track_title)
            html = await self._get_html(url)
            soup = BeautifulSoup(html, "html.parser")

            lyrics_containers = soup.select("div[data-lyrics-container='true']")

            if not lyrics_containers:
                raise LyricsScraperException(f"Lyrics not found for {artist_name} - {track_title}")

            cleaned_lyrics = []

            for container in lyrics_containers:
                section = ""
                for element in container.contents:
                    if isinstance(element, Tag):
                        if element.name in ["br", "i", "b"]:
                            section += str(element)
                        elif element.name == "a":
                            for el in element.find("span"):
                                section += str(el)
                    else:
                        section += str(element)

                cleaned_lyrics.append(section)

            lyrics = "<br/>".join(cleaned_lyrics)

            print(f"Success: {url}")
            return lyrics
        except LyricsScraperException as e:
            print(f"Failure: {url}")
            print(e)
            raise
        except Exception as e:
            print(f"Failure: {url}")
            print(e)
            raise LyricsScraperException(f"An error occurred while scraping the lyrics")

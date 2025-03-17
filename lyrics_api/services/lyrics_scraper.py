import asyncio
import random
import string
import unicodedata

import httpx
import re
from bs4 import BeautifulSoup, Tag
from httpx import Response


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
    def _format_string_for_url(s: str) -> str:
        """
        Formats the input string into appropriate format.

        Parameters
        ----------
        s : str
            The string to format.

        Returns
        -------
        str
            The formatted string suitable for URL construction.
        """

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

    def _get_url(self, artist: str, title: str) -> str:
        """
        Generates a formatted URL for retrieving lyrics.

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
        """

        artist = self._format_string_for_url(artist)
        title = self._format_string_for_url(title)

        artist = artist[0].upper() + artist[1:]

        return f"/{artist}-{title}-lyrics"

    async def _make_limited_request(self, url: str, delay: float) -> Response:
        """
        Makes an asynchronous HTTP GET request with concurrency control.

        The request is rate-limited using a semaphore to control the number of concurrent
        requests. A random delay is added before making the request to reduce the likelihood
        of triggering anti-scraping mechanisms.

        Parameters
        ----------
        url : str
            The URL to send the GET request to.

        Returns
        -------
        Response
            The HTTP response object received from the request.

        Raises
        ------
        httpx.RequestError
            If there is a network-related issue during the request.
        httpx.HTTPStatusError
            If the server returns a non-2XX HTTP status code.
        """

        async with self.semaphore:
            await asyncio.sleep(delay)
            response = await self.client.get(url=url, follow_redirects=True)

        return response

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
            If the request fails or another exception occurs.
        """

        try:
            response = await self._make_limited_request(url=url, delay=random.uniform(0.25, 1))
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            message = f"Non-2XX status code - {e}"
            print(message)
            raise LyricsScraperException(message)
        except httpx.RequestError as e:
            message = f"Request failed - {e}"
            print(message)
            raise LyricsScraperException(message)
        except Exception as e:
            message = f"Failed to retrieve HTML - {e}"
            print(message)
            raise LyricsScraperException(message)

    @staticmethod
    def _extract_lyrics_containers(html: str) -> list[Tag]:
        """
        Extracts lyric containers from the provided HTML.

        The function searches for `<div>` elements with the attribute `data-lyrics-container="true"`which typically
        contains the lyrics on the target website.

        Parameters
        ----------
        html : str
            The raw HTML content of the lyrics page.

        Returns
        -------
        list of Tag objects
            A list of BeautifulSoup `Tag` objects containing the lyrics.
        """

        soup = BeautifulSoup(html, "html.parser")
        lyrics_containers = soup.select("div[data-lyrics-container='true']")

        return lyrics_containers

    @staticmethod
    def _clean_lyrics_text(lyrics_containers: list[Tag]) -> str:
        """
        Cleans and formats the extracted lyrics.

        This method processes the extracted HTML elements containing the lyrics, preserving
        formatting elements such as `<br>`, `<i>`, and `<b>`. Hyperlinks are handled by extracting
        their inner text.

        Parameters
        ----------
        lyrics_containers : list of Tag
            A list of BeautifulSoup `Tag` objects containing the lyrics.

        Returns
        -------
        str
            The cleaned lyrics, formatted as an HTML string with line breaks.
        """

        cleaned_lyrics = []

        for container in lyrics_containers:
            section = ""

            for element in container.contents:
                if isinstance(element, Tag):
                    if element.name in ["br", "i", "b"]:
                        section += str(element)
                    elif element.name == "a":
                        section += "".join([str(el) for el in element.find("span")])
                else:
                    section += str(element)

            cleaned_lyrics.append(section)

        return "<br/>".join(cleaned_lyrics)

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

        url = None

        try:
            url = self._get_url(artist_name, track_title)
            html = await self._get_html(url)
            lyrics_containers = self._extract_lyrics_containers(html)

            if not lyrics_containers:
                raise LyricsScraperException(f"Lyrics containers not found for {artist_name} - {track_title}")

            lyrics = self._clean_lyrics_text(lyrics_containers)

            if not lyrics:
                raise LyricsScraperException(f"Lyrics not found for {artist_name} - {track_title}")

            print(f"Successfully scraped lyrics for {artist_name} - {track_title}")

            return lyrics
        except LyricsScraperException as e:
            print(f"Failure: {url}")
            print(e)
            raise
        except Exception as e:
            print(f"Failure: {url}")
            print(e)
            raise LyricsScraperException(f"An error occurred while scraping the lyrics")

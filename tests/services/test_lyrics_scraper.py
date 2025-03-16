import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest

from lyrics_api.services.lyrics_scraper import LyricsScraper


# 1. Test _format_string_for_url returns expected string.
# 2. Test _get_url returns expected url.
# 3. Test _make_limited_request calls httpx AsyncClient get method.
# 4. Test _make_limited_request stops more than semaphore limit requests occuring simultaneously.
# 5. Test _get_html raises LyricsScraperException if request fails.
# 6. Test _get_html raises LyricsScraperException if response status code not 2XX.
# 7. Test _get_html returns expected string.
# 8. Test _extract_lyrics_containers returns an empty list if no lyrics containers found.
# 9. Test _extract_lyrics_containers returns expected list.
# 10. Test _clean_lyrics_text removes all tags except <br>, <i> and <b> and keeps all raw text.
# 11. Test scrape_lyrics raises LyricsScraperException if no lyrics containers found.
# 12. Test scrape_lyrics raises LyricsScraperException if exception occurs in _get_url.
# 13. Test scrape_lyrics raises LyricsScraperException if exception occurs in _get_html.
# 14. Test scrape_lyrics raises LyricsScraperException if exception occurs in _extract_lyrics_containers.
# 15. Test scrape_lyrics raises LyricsScraperException if exception occurs in _clean_lyrics_text.


@pytest.fixture
def lyrics_scraper() -> LyricsScraper:
    """Fixture to provide a LyricsScraper instance with a mock client and semaphore."""

    semaphore = asyncio.Semaphore(10)
    client = AsyncMock(spec=httpx.AsyncClient)
    scraper = LyricsScraper(semaphore=semaphore, client=client)
    return scraper


@pytest.mark.parametrize("input_str, expected", [
    ("Beyoncé", "beyonce"),
    ("AC/DC", "acdc"),
    ("Drake & Future", "drake-and-future"),
    ("Eminem feat. Rihanna", "eminem"),
    ("Love (Remix)", "love-remix"),
    ("Måneskin", "maneskin"),
    ("Chri$tian Gate$", "chri-tian-gate"),
    ("AFRAID TO DIE (feat. Tatiana Shmayluyk from Jinjer)", "afraid-to-die"),
    (
            "Electric Touch (feat. Fall Out Boy) (Taylor’s Version) (From The Vault)",
            "electric-touch-taylors-version-from-the-vault"
    )
])
def test_format_string_for_url(lyrics_scraper, input_str, expected):
    """Test the formatting of strings for URLs."""

    assert lyrics_scraper._format_string_for_url(input_str) == expected


@pytest.mark.parametrize("artist, title, expected", [
    ("The Beatles", "Hey Jude", "/The-beatles-hey-jude-lyrics"),
    ("Beyoncé", "Halo", "/Beyonce-halo-lyrics"),
    ("AC/DC", "Back in Black", "/Acdc-back-in-black-lyrics"),
    ("Eminem feat. Rihanna", "Love the Way You Lie", "/Eminem-love-the-way-you-lie-lyrics"),
    ("Drake & Future", "Life Is Good", "/Drake-and-future-life-is-good-lyrics"),
])
def test_get_url(lyrics_scraper, artist, title, expected):
    """Test that URLs are correctly formatted."""

    assert lyrics_scraper._get_url(artist, title) == expected

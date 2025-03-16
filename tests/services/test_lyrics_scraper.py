import asyncio
import time
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from bs4 import BeautifulSoup

from lyrics_api.services.lyrics_scraper import LyricsScraper, LyricsScraperException


# 11. Test scrape_lyrics raises LyricsScraperException if no lyrics containers found.
# 12. Test scrape_lyrics raises LyricsScraperException if exception occurs in _get_url.
# 13. Test scrape_lyrics raises LyricsScraperException if exception occurs in _get_html.
# 14. Test scrape_lyrics raises LyricsScraperException if exception occurs in _extract_lyrics_containers.
# 15. Test scrape_lyrics raises LyricsScraperException if exception occurs in _clean_lyrics_text.


@pytest.fixture
def mock_client() -> AsyncMock:
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def lyrics_scraper(mock_client) -> LyricsScraper:
    """Fixture to provide a LyricsScraper instance with a mock client and semaphore."""

    semaphore = asyncio.Semaphore(10)
    scraper = LyricsScraper(semaphore=semaphore, client=mock_client)
    return scraper


# -------------------- FORMAT STRING FOR URL -------------------- #
# 1. Test _format_string_for_url returns expected string.
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


# -------------------- GET URL -------------------- #
# 2. Test _get_url returns expected url.
@pytest.mark.parametrize("artist, title, expected", [
    ("The Beatles", "Hey Jude", "/The-beatles-hey-jude-lyrics"),
    ("Beyoncé", "Halo", "/Beyonce-halo-lyrics"),
    ("AC/DC", "Back in Black", "/Acdc-back-in-black-lyrics"),
    ("Eminem feat. Rihanna", "Love the Way You Lie", "/Eminem-love-the-way-you-lie-lyrics"),
    ("Drake & Future", "Life Is Good", "/Drake-and-future-life-is-good-lyrics"),
    (
            "Taylor Swift",
            "Electric Touch (feat. Fall Out Boy) (Taylor’s Version) (From The Vault)",
            "/Taylor-swift-electric-touch-taylors-version-from-the-vault-lyrics"
    )
])
def test_get_url(lyrics_scraper, artist, title, expected):
    """Test that URLs are correctly formatted."""

    assert lyrics_scraper._get_url(artist, title) == expected


# -------------------- MAKE LIMITED REQUEST -------------------- #
# 3. Test _make_limited_request calls httpx AsyncClient get method.
# 4. Test _make_limited_request stops more than semaphore limit requests occuring simultaneously.
@pytest.mark.asyncio
async def test_make_limited_request(lyrics_scraper, mock_client):
    """Test that _make_limited_request properly makes a GET request."""

    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = "<html></html>"
    mock_client.get.return_value = mock_response
    url = "https://example.com/test"

    response = await lyrics_scraper._make_limited_request(url=url, delay=0)

    assert response.status_code == 200
    assert response.text == "<html></html>"
    mock_client.get.assert_called_with(url=url, follow_redirects=True)


@pytest.mark.asyncio
async def test_make_limited_request_restricts_concurrent_requests(lyrics_scraper, mock_client):
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = "<html></html>"
    mock_client.get.return_value = mock_response
    url = "https://example.com/test"
    # create tasks
    tasks = [lyrics_scraper._make_limited_request(url=url, delay=0.25) for _ in range(5)]
    # set semaphore counter to value equal to tasks length
    lyrics_scraper.semaphore = asyncio.Semaphore(5)

    start_unrestricted = time.perf_counter()
    await asyncio.gather(*tasks)
    end_unrestricted = time.perf_counter()
    diff_unrestricted = end_unrestricted - start_unrestricted

    # create tasks
    tasks = [lyrics_scraper._make_limited_request(url=url, delay=0.25) for _ in range(5)]
    # reduce semaphore counter to value below tasks length
    lyrics_scraper.semaphore = asyncio.Semaphore(3)
    start_restricted = time.perf_counter()
    await asyncio.gather(*tasks)
    end_restricted = time.perf_counter()
    diff_restricted = end_restricted - start_restricted

    assert diff_restricted > diff_unrestricted


# -------------------- GET HTML -------------------- #
# 5. Test _get_html raises LyricsScraperException if request fails.
# 6. Test _get_html raises LyricsScraperException if general exception occurs.
# 7. Test _get_html returns expected string.
@pytest.mark.asyncio
async def test_get_html_request_failure(lyrics_scraper):
    mock_method = AsyncMock()
    mock_method.side_effect = httpx.RequestError("Test")
    lyrics_scraper._make_limited_request = mock_method
    url = "https://example.com/test"

    with pytest.raises(LyricsScraperException, match="Request failed"):
        await lyrics_scraper._get_html(url=url)


@pytest.mark.asyncio
async def test_get_html_request_failure(lyrics_scraper):
    mock_method = AsyncMock()
    mock_method.side_effect = Exception("Test")
    lyrics_scraper._make_limited_request = mock_method
    url = "https://example.com/test"

    with pytest.raises(LyricsScraperException, match="Failed to retrieve HTML"):
        await lyrics_scraper._get_html(url=url)


@pytest.mark.asyncio
async def test_get_html_success(lyrics_scraper):
    """Test successful retrieval of HTML content."""
    mock_response = Mock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.text = "<html>Test</html>"
    mock_method = AsyncMock()
    mock_method.return_value = mock_response
    lyrics_scraper._make_limited_request = mock_method
    url = "https://example.com/test"

    html = await lyrics_scraper._get_html(url)

    assert html == "<html>Test</html>"


# -------------------- EXTRACT LYRICS CONTAINERS -------------------- #
# 1. Test _extract_lyrics_containers returns expected list where tags have data-lyrics-container data attribute set.
@pytest.mark.parametrize(
    "html_input, expected_output",
    [
        (
                """
                    <html>
                        <body>
                            <div data-lyrics-container="true">First line of lyrics</div>
                            <div data-lyrics-container="true">Second line of lyrics</div>
                        </body>
                    </html>
                """,
                [
                    '<div data-lyrics-container="true">First line of lyrics</div>',
                    '<div data-lyrics-container="true">Second line of lyrics</div>'
                ]
        ),
        (
                """
                    <html>
                        <body>
                            <div class="data-lyrics-container">First line of lyrics</div>
                            <div>Second line of lyrics</div>
                        </body>
                    </html>
                """,
                []
        ),
    ]
)
def test_extract_lyrics_containers_returns_expected_list(lyrics_scraper, html_input, expected_output):
    res = lyrics_scraper._extract_lyrics_containers(html_input)

    assert [str(entry) for entry in res] == expected_output


# -------------------- CLEAN LYRICS TEXT -------------------- #
# 10. Test _clean_lyrics_text removes all tags except <br>, <i> and <b> and keeps all raw text.
@pytest.mark.parametrize(
    "html_input, expected_output",
    [
        (
                """
                <div data-lyrics-container="true">First line of lyrics</div>
                <div data-lyrics-container="true">Second line of lyrics</div>
                """,
                "First line of lyrics<br/>Second line of lyrics"
        ),
        (

                "",
                ""
        ),
        (

                """<div data-lyrics-container="true">[Bridge: Demi Lovato & <i>John O'Callaghan</i>]<br/></div>""",
                "[Bridge: Demi Lovato & <i>John O'Callaghan</i>]<br/>"
        ),
        (
                """<div data-lyrics-container="true">(<i>You're all that I see, you're all that I see</i>)</div>""",
                "(<i>You're all that I see, you're all that I see</i>)"
        ),
        (
                """<div data-lyrics-container="true">(<b>You're all that I see, you're all that I see</b>)</div>""",
                "(<b>You're all that I see, you're all that I see</b>)"
        ),
        (
                """<div data-lyrics-container="true"><span class="test">Random text</span></div>""",
                ""
        ),
(
                """<div data-lyrics-container="true"><a><span class="test">Random text</span></a></div>""",
                "Random text"
        ),
    ]
)
def test_clean_lyrics_text_returns_expected_string(lyrics_scraper, html_input, expected_output):
    soup = BeautifulSoup(html_input, "html.parser")
    containers = soup.select("div[data-lyrics-container='true']")
    res = lyrics_scraper._clean_lyrics_text(containers)

    assert res == expected_output

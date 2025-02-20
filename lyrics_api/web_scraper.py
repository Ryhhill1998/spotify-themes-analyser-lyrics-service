import requests
from bs4 import BeautifulSoup

class WebScraper:

    def __init__(self):
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        }

    def scrape_lyrics(self, url: str) -> str:
        
        response = requests.get(url, headers=self.header)

        if response.status_code != 200:
            return "Failed to fetch page"

        soup = BeautifulSoup(response.text, "html.parser")
        lyrics_container = soup.select_one("div.container.main-page div.row div.col-xs-12.col-lg-8.text-center")

        if not lyrics_container:
            return "Lyrics not found"
        
        lyrics_div = lyrics_container.find_all("div")[5]
        lyrics = lyrics_div.get_text(separator=" ").strip()

        return lyrics

    def get_url(self, artist: str, title: str) -> str:

        url=f"https://www.azlyrics.com/lyrics/{artist}/{title}.html"

        return url
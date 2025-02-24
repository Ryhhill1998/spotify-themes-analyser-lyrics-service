import requests
from bs4 import BeautifulSoup
import urllib.parse

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
    

    def _get_lyrics_html(self, artist: str, track_title: str):

        url=self._get_url(artist, track_title)
        response = requests.get(url, headers=self.headers)

        if response.status_code==200:
            html=response.text

        elif response.status_code==404:
            html=self._search_html(artist, track_title)
        else:
            raise LyricsScraperException("Lyrics not found")
        
        return html


    def _get_url(self, artist: str, title: str) -> str:

        def format_string(string: str):
            return string.lower().replace(" ", "")

        artist = format_string(artist)
        title = format_string(title)
        url=f"{self.base_url}/{artist}/{title}.html"

        return url
    
    def _search_html(self, artist: str, track_title: str):

        url = "https://www.azlyrics.com/"
        html = self._get_html(url)
        soup = BeautifulSoup(html, "html.parser")
        x_selector = soup.select_one("form.navbar-form.navbar-right.search input[name='x']")

        if x_selector is None:
            raise LyricsScraperException("Search form input 'x' not found")
        
        x_value = x_selector.get("value")
        base_url = "https://search.azlyrics.com/search.php"
        query_params=urllib.parse.urlencode({"q":f"{artist} {track_title}", "x": x_value})
        whole_url=f"{base_url}/?{query_params}"
        top_search = self._get_html(whole_url)
        new_soup = BeautifulSoup(top_search, "html.parser")
        title_selector = new_soup.select_one("body > div.container.main-page > div > div > div.panel > table > tbody > tr > td > a")

        if title_selector is None:
            raise LyricsScraperException("No search results found for the given artist and track title")
        
        title_link = title_selector.get("href")
                
        lyrics_url = self._get_html(title_link)
        return lyrics_url

        
        # get href of top search results 
        # return html of the href page 
        


    def scrape_lyrics(self, artist: str, track_title: str) -> str:
        
        try:
            
            html =self._get_lyrics_html(artist, track_title)
            soup = BeautifulSoup(html, "html.parser")
            lyrics_container = soup.select_one("div.container.main-page div.row div.col-xs-12.col-lg-8.text-center")
            
            if not lyrics_container:

                raise LyricsScraperException("Lyrics not found")

            lyrics_div = lyrics_container.find_all("div")[5]
            lyrics = lyrics_div.get_text().strip()

            return lyrics

        except Exception: 
        
            raise LyricsScraperException(f"An error occurred while scraping the lyrics")

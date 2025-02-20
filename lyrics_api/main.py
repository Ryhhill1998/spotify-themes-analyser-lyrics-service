from fastapi import FastAPI, HTTPException
from web_scraper import WebScraper
import uvicorn

app = FastAPI()
scraper = WebScraper()

@app.get('/get_lyrics')
async def get_lyrics(artist: str, track_title: str):
        
    url = scraper.get_url(artist, track_title)
    lyrics =scraper.scrape_lyrics(url)

    if lyrics == "Failed to fetch page" or lyrics == "Lyrics not found":
        raise HTTPException(status_code=404, detail=lyrics)

    return {"artist": artist, "track_title": track_title, "lyrics": lyrics}

def main():
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()
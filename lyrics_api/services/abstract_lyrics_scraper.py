import asyncio
import random
from abc import ABC, abstractmethod

import httpx


class AbstractLyricsScraper(ABC):
    def __init__(self, semaphore: asyncio.Semaphore, client: httpx.AsyncClient):
        self.semaphore = semaphore
        self.client = client

    async def _get_html(self, url: str) -> str:
        async with self.semaphore:
            await asyncio.sleep(random.uniform(0.25, 1))
            response = await self.client.get(url=url, follow_redirects=True)

        response.raise_for_status()

        return response.text

    @abstractmethod
    async def scrape_lyrics(self, artist_name: str, track_title: str) -> str:
        pass

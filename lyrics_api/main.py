import asyncio
import sys
from contextlib import asynccontextmanager

import aiosqlite
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from lyrics_api.services.storage.storage_service import initialise_db
from lyrics_api.settings import Settings
from lyrics_api.services.lyrics_scraper import LyricsScraper
from lyrics_api.routers import lyrics


def initialise_logger():
    logger.remove()
    logger.add(sys.stdout, format="{time} {level} {message}", level="INFO")
    logger.add(sys.stderr, format="{time} {level} {message}", level="ERROR")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()

    initialise_logger()

    # initialise database
    db = await aiosqlite.connect(settings.db_path)
    await initialise_db(db)
    await db.close()

    semaphore = asyncio.Semaphore(settings.max_concurrent_scrapes)
    httpx_client = httpx.AsyncClient(base_url=settings.base_url, headers=settings.headers)

    try:
        app.state.lyrics_scraper = LyricsScraper(semaphore=semaphore, client=httpx_client)

        yield
    finally:
        await httpx_client.aclose()


app = FastAPI(lifespan=lifespan)


# healthcheck route
@app.get("/")
def health_check():
    return {"status": "running"}


app.include_router(lyrics.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, e: Exception):
    """Handles all unhandled exceptions globally."""
    logger.exception(f"Unhandled Exception occurred at {request.url} - {e}")

    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong. Please try again later."},
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all incoming requests."""

    ip_addr = request.client.host
    port = request.client.port
    url = request.url
    req_method = request.method

    log_message = f"{ip_addr}:{port} made {req_method} request to {url}."

    logger.info(log_message)

    response = await call_next(request)
    return response

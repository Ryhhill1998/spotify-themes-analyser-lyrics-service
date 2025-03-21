from unittest.mock import AsyncMock, Mock

import aiosqlite
import pytest
import pytest_asyncio

from lyrics_api.services.storage.storage_service import initialise_db, StorageServiceException, StorageService

DB_PATH = ":memory:"


@pytest_asyncio.fixture
async def db():
    """Creates an in-memory SQLite database for testing."""

    db = await aiosqlite.connect(DB_PATH)
    await initialise_db(db)

    yield db

    await db.close()


@pytest.fixture
def storage_service(db) -> StorageService:
    return StorageService(db)


@pytest_asyncio.fixture
async def existing_track(db):
    insert_statement = f"""
        INSERT INTO Lyrics (track_id, lyrics)
        VALUES (?, ?);
    """

    track_id = "1"
    lyrics = "Lyrics for track 1"

    data_to_insert = (track_id, lyrics)
    await db.execute(insert_statement, data_to_insert)
    await db.commit()

    return track_id, lyrics


# -------------------- INITIALISE DB -------------------- #
# 1. Test that initialise_db creates a new table with expected columns.
@pytest.mark.asyncio
async def test_initialise_db_creates_table():
    """Test that initialise_db creates a new table with expected columns."""

    async with aiosqlite.connect(DB_PATH) as db:
        await initialise_db(db)

        # Query database metadata to check if 'Lyrics' table exists
        async with db.execute("PRAGMA table_info(Lyrics);") as cursor:
            columns = await cursor.fetchall()

        # Extract column names from PRAGMA query results
        column_names = {col[1] for col in columns}

        assert column_names == {"track_id", "lyrics"}, "Table should have 'track_id' and 'lyrics' columns"


# -------------------- STORE LYRICS -------------------- #
# 1. Test that store_lyrics raises StorageServiceException if track_id already exists.
# 2. Test that store_lyrics raises StorageServiceException if operational error occurs.
# 3. Test that store_lyrics raises StorageServiceException if database error occurs.
# 4. Test that store_lyrics stores lyrics in database.
@pytest.mark.asyncio
async def test_store_lyrics_track_already_exists(storage_service, existing_track):
    """Ensure StorageServiceException is raised on duplicate track ID."""

    existing_track_id, existing_lyrics = existing_track

    # insert should fail due to primary key violation
    with pytest.raises(StorageServiceException, match="Track ID '1' already exists."):
        await storage_service.store_lyrics(track_id=existing_track_id, lyrics="Random lyrics")


@pytest.mark.asyncio
async def test_store_lyrics_operational_error(storage_service, existing_track, db):
    """Test retrieving lyrics when a DB operational error occurs."""

    mock_execute = AsyncMock()
    mock_execute.side_effect = aiosqlite.OperationalError
    db.execute = mock_execute

    with pytest.raises(StorageServiceException, match="Database operation failed"):
        await storage_service.store_lyrics(track_id="2", lyrics="Lyrics for track 2")


@pytest.mark.asyncio
async def test_store_lyrics_database_error(storage_service, existing_track, db):
    """Test retrieving lyrics when a DB operational error occurs."""

    mock_execute = AsyncMock()
    mock_execute.side_effect = aiosqlite.DatabaseError
    db.execute = mock_execute

    with pytest.raises(StorageServiceException, match="Unexpected database error"):
        await storage_service.store_lyrics(track_id="2", lyrics="Lyrics for track 2")


@pytest.mark.asyncio
async def test_store_lyrics_adds_lyrics_to_db(storage_service, db):
    """Test that store lyrics adds lyrics to db"""

    track_id = "1"
    lyrics = "Lyrics for track 1"

    await storage_service.store_lyrics(track_id=track_id, lyrics=lyrics)

    cursor = await db.execute(f"SELECT * FROM Lyrics WHERE track_id = {track_id}")
    row = await cursor.fetchone()
    assert row == (track_id, lyrics)


# -------------------- RETRIEVE LYRICS -------------------- #
# 1. Test that retrieve_lyrics raises StorageServiceException if operational error occurs.
# 2. Test that retrieve_lyrics raises StorageServiceException if database error occurs.
# 3. Test that retrieve_lyrics returns None if track_id not found.
# 4. Test that retrieve_lyrics returns expected lyrics.
@pytest.mark.asyncio
async def test_retrieve_lyrics_operational_error(storage_service, existing_track, db):
    """Test retrieving lyrics when a DB operational error occurs."""

    mock_execute = AsyncMock()
    mock_execute.side_effect = aiosqlite.OperationalError
    db.execute = mock_execute

    with pytest.raises(StorageServiceException, match="Database operation failed"):
        await storage_service.retrieve_lyrics(track_id="1")


@pytest.mark.asyncio
async def test_retrieve_lyrics_database_error(storage_service, existing_track, db):
    """Test retrieving lyrics when a DB operational error occurs."""

    mock_execute = AsyncMock()
    mock_execute.side_effect = aiosqlite.DatabaseError
    db.execute = mock_execute

    with pytest.raises(StorageServiceException, match="Unexpected database error"):
        await storage_service.retrieve_lyrics(track_id="1")


@pytest.mark.asyncio
async def test_retrieve_lyrics_does_not_exist(storage_service):
    """Test retrieving lyrics for a track that doesn't exist."""

    retrieved_lyrics = await storage_service.retrieve_lyrics("does_not_exist")

    assert retrieved_lyrics is None, "Should return None for non-existent track"


@pytest.mark.asyncio
async def test_retrieve_lyrics_does_exist(storage_service, existing_track):
    """Test retrieving lyrics for a track that does exist."""

    existing_track_id, existing_lyrics = existing_track

    retrieved_lyrics = await storage_service.retrieve_lyrics(existing_track_id)

    assert retrieved_lyrics == existing_lyrics, "Should return stored lyrics for stored track"

import aiosqlite
import pytest
import pytest_asyncio

from lyrics_api.services.storage.storage_service import initialise_db, StorageServiceException, StorageService

DB_PATH = ":memory:"


@pytest_asyncio.fixture
async def db_connection():
    """Creates an in-memory SQLite database for testing."""

    db = await aiosqlite.connect(DB_PATH)
    await initialise_db(db)

    yield db

    await db.close()


@pytest.fixture
def storage_service(db_connection) -> StorageService:
    return StorageService(db_connection)


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
async def test_store_duplicate_track_id_raises_exception(storage_service):
    """Ensure StorageServiceException is raised on duplicate track ID."""
    track_id = "duplicate"
    lyrics = "This is a song."

    await storage_service.store_lyrics(track_id, lyrics)  # First insert should work

    # Second insert should fail due to primary key violation
    with pytest.raises(StorageServiceException, match="Track ID 'duplicate' already exists."):
        await storage_service.store_lyrics(track_id, lyrics)


# -------------------- RETRIEVE LYRICS -------------------- #
# 1. Test that retrieve_lyrics raises StorageServiceException if operational error occurs.
# 2. Test that retrieve_lyrics raises StorageServiceException if database error occurs.
# 3. Test that retrieve_lyrics returns expected lyrics.
@pytest.mark.asyncio
async def test_retrieve_non_existent_lyrics(storage_service):
    """Test retrieving lyrics for a track that doesn't exist."""

    track_id = "non-existent"

    retrieved_lyrics = await storage_service.retrieve_lyrics(track_id)

    assert retrieved_lyrics is None, "Should return None for non-existent track"

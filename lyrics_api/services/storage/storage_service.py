import aiosqlite


async def initialise_db(db: aiosqlite.Connection):
    """Creates the required database tables if they don't exist."""

    await db.executescript("""
        CREATE TABLE IF NOT EXISTS Lyrics (
            track_id TEXT PRIMARY KEY,
            lyrics TEXT
        );
    """)

    await db.commit()


class StorageServiceException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class StorageService:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def store_lyrics(self, track_id: str, lyrics: str):
        insert_statement = f"""
            INSERT INTO Lyrics (track_id, lyrics)
            VALUES (?, ?);
        """

        data_to_insert = (track_id, lyrics)

        try:
            await self.db.execute(insert_statement, data_to_insert)
            await self.db.commit()
        except aiosqlite.IntegrityError:
            raise StorageServiceException(f"Track ID '{track_id}' already exists.")
        except aiosqlite.OperationalError as e:
            raise StorageServiceException(f"Database operation failed: {e}")
        except aiosqlite.DatabaseError as e:
            raise StorageServiceException(f"Unexpected database error: {e}")

    async def retrieve_lyrics(self, track_id: str) -> str | None:
        select_query = f"""
            SELECT * FROM Lyrics 
            WHERE track_id = ?;
        """

        try:
            async with self.db.execute(select_query, (track_id,)) as cursor:
                row = await cursor.fetchone()
                return row[1] if row else None
        except aiosqlite.OperationalError as e:
            raise StorageServiceException(f"Database operation failed: {e}")
        except aiosqlite.DatabaseError as e:
            raise StorageServiceException(f"Unexpected database error: {e}")

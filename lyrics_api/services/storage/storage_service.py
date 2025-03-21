import aiosqlite


async def initialise_db(db: aiosqlite.Connection):
    """
    Creates the required database tables if they don't exist.

    This function initializes the `Lyrics` table, ensuring it has the correct schema.

    Parameters
    ----------
    db : aiosqlite.Connection
        The SQLite database connection.

    Raises
    ------
    aiosqlite.Error
        If an error occurs while creating the table.
    """

    await db.executescript("""
        CREATE TABLE IF NOT EXISTS Lyrics (
            track_id TEXT PRIMARY KEY,
            lyrics TEXT
        );
    """)

    await db.commit()


class StorageServiceException(Exception):
    """
    Custom exception for errors occurring in the StorageService.

    This exception is raised when database operations fail, such as integrity violations or unexpected database errors.
    """

    def __init__(self, message: str):
        super().__init__(message)


class StorageService:
    """
    Provides methods to store and retrieve song lyrics from an SQLite database.

    This service manages a `Lyrics` table that stores lyrics associated with track IDs.

    Attributes
    ----------
    db : aiosqlite.Connection
        The SQLite database connection used for executing queries.

    Methods
    -------
    store_lyrics(track_id: str, lyrics: str)
        Stores lyrics for a given track in the database.
    retrieve_lyrics(track_id: str) -> str | None
        Retrieves lyrics for a given track from the database.
    """

    def __init__(self, db: aiosqlite.Connection):
        """
        Attributes
        ----------
        db : aiosqlite.Connection
            The SQLite database connection.
        """

        self.db = db

    async def store_lyrics(self, track_id: str, lyrics: str):
        """
        Stores lyrics for a given track in the database.

        If the track ID already exists, raises a `StorageServiceException`.

        Parameters
        ----------
        track_id : str
            The unique identifier for the track.
        lyrics : str
            The lyrics associated with the track.

        Raises
        ------
        StorageServiceException
            If the track ID already exists or if a database error occurs.
        """

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
            raise StorageServiceException(f"Database operation failed - {e}")
        except aiosqlite.DatabaseError as e:
            raise StorageServiceException(f"Unexpected database error - {e}")

    async def retrieve_lyrics(self, track_id: str) -> str | None:
        """
        Retrieves lyrics for a given track from the database.

        Parameters
        ----------
        track_id : str
            The unique identifier for the track.

        Returns
        -------
        str or None
            The lyrics if found, otherwise None.

        Raises
        ------
        StorageServiceException
            If a database error occurs.
        """

        select_query = f"""
            SELECT * FROM Lyrics 
            WHERE track_id = ?;
        """

        try:
            cursor = await self.db.execute(select_query, (track_id,))
            row = await cursor.fetchone()
            await cursor.close()
            lyrics = row[1] if row else None

            return lyrics
        except aiosqlite.OperationalError as e:
            raise StorageServiceException(f"Database operation failed - {e}")
        except aiosqlite.DatabaseError as e:
            raise StorageServiceException(f"Unexpected database error - {e}")

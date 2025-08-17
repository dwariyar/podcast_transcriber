# Standard library imports
import sqlite3 # For interacting with a local SQLite database to store transcripts

class DatabaseManager:
    """
    A class to manage interactions with the SQLite database for podcast transcripts.
    """

    def __init__(self, db_path="podcast_transcripts.db"):
        """
        Initializes the DatabaseManager.

        Args:
            db_path (str, optional): Path to the SQLite database file.
                                     Defaults to "podcast_transcripts.db".
        """
        self.db_path = db_path
        self._init_database_table() # Ensure the table exists on initialization

    def _init_database_table(self):
        """
        Initializes the SQLite database table.
        Creates the 'episodes' table if it doesn't already exist,
        with columns for id, title, and transcript.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute('''
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                transcript TEXT
            )
            ''')
            conn.commit()
            print(f"SQLite database initialized at: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Error initializing database table: {e}")
            conn.rollback()
        finally:
            conn.close()

    def save_transcript(self, title, transcript):
        """
        Saves the episode title and its transcribed text to the SQLite database.

        Args:
            title (str): The title of the podcast episode.
            transcript (str): The transcribed text of the episode.
        """
        if not title or not transcript:
            print("Title or transcript is empty, skipping database save.")
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO episodes (title, transcript) VALUES (?, ?)", (title, transcript))
            conn.commit()
            print(f"Saved '{title}' to database.")
        except sqlite3.Error as e:
            print(f"SQLite error saving '{title}': {e}")
            conn.rollback()
        finally:
            conn.close()

    def fetch_all_transcripts(self):
        """
        Retrieves all episode records from the database and returns them
        as a list of dictionaries, compatible with the Algolia uploader.

        Returns:
            list: A list of dictionaries, where each dictionary represents an episode record.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        records = []
        try:
            c.execute("SELECT id, title, transcript FROM episodes")
            raw_records = c.fetchall()
            
            # Convert tuples to dictionaries with keys expected by Algolia Uploader
            records = [
                {
                    "objectID": str(rec[0]), # Using the unique 'id' as objectID
                    "title": rec[1],
                    "transcription": rec[2]
                }
                for rec in raw_records
            ]
            print(f"Fetched {len(records)} records from database.")
        except sqlite3.Error as e:
            print(f"Error retrieving records from database: {e}")
        finally:
            conn.close()
        return records

    def clear_all_transcripts(self):
        """
        Deletes all records from the 'podcast_transcripts' table.
        This effectively clears the database for new runs.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM podcast_transcripts")
            conn.commit()
            print("All previous transcripts cleared from the database.")
        except sqlite3.Error as e:
            print(f"Error clearing database: {e}")
            conn.rollback()
        finally:
            conn.close()

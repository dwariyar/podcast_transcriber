# Standard library imports
import sqlite3 # For interacting with a local SQLite database to store transcripts
import os # Not directly used in this snippet but commonly imported in this file

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
        self._create_table() # Ensure the table exists on initialization

    def _get_connection(self):
        """
        Returns a new database connection.
        This method is now a central point for obtaining connections.
        """
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        """
        Initializes the SQLite database table.
        Creates the 'podcast_transcripts' table if it doesn't already exist,
        with columns for title and transcript.
        """
        conn = self._get_connection() # Use the new _get_connection method
        try:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS podcast_transcripts (
                title TEXT PRIMARY KEY,
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
        Uses INSERT OR REPLACE to update if title exists, or insert if new.

        Args:
            title (str): The title of the podcast episode.
            transcript (str): The transcribed text of the episode.
        """
        if not title or not transcript:
            print("Title or transcript is empty, skipping database save.")
            return

        conn = self._get_connection() # Use the new _get_connection method
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO podcast_transcripts (title, transcript) VALUES (?, ?)
            ''', (title, transcript))
            conn.commit()
            print(f"Saved '{title}' to database.")
        except sqlite3.Error as e:
            print(f"SQLite error saving '{title}': {e}")
            conn.rollback() # Rollback changes if an error occurs
        finally:
            conn.close()

    def fetch_all_transcripts(self):
        """
        Retrieves all episode records (title, transcript) from the database.

        Returns:
            list: A list of dictionaries, where each dictionary represents a record
                  with keys 'objectID', 'title', and 'transcription', suitable for Algolia.
        """
        conn = self._get_connection() # Use the new _get_connection method
        records = []
        try:
            # Use row_factory to get dict-like rows
            conn.row_factory = sqlite3.Row 
            cursor = conn.cursor()
            cursor.execute("SELECT title, transcript FROM podcast_transcripts")
            raw_records = cursor.fetchall()
            
            records = [
                {
                    "objectID": rec['title'], # Using title as objectID for consistency with save_transcript's PRIMARY KEY
                    "title": rec['title'],
                    "transcription": rec['transcript']
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
        conn = self._get_connection() # Use the new _get_connection method
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
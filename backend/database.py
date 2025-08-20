# Standard library imports
import sqlite3 # For interacting with a local SQLite database to store transcripts
import os # Not directly used in this snippet but commonly imported in this file
from datetime import datetime # For recording job creation/update timestamps

class DatabaseManager:
    """
    A class to manage interactions with the SQLite database for podcast transcripts and job queue.
    """

    def __init__(self, db_path="podcast_transcripts.db"):
        """
        Initializes the DatabaseManager.

        Args:
            db_path (str, optional): Path to the SQLite database file.
                                     Defaults to "podcast_transcripts.db".
        """
        self.db_path = db_path
        self._create_tables() # Ensure both tables exist on initialization

    def _get_connection(self):
        """Returns a new database connection."""
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        """
        Initializes the SQLite database tables: 'podcast_transcripts' and 'jobs'.
        Creates them if they don't already exist.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Table for podcast transcripts
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS podcast_transcripts (
                title TEXT PRIMARY KEY,
                transcript TEXT
            )
            ''')
            
            # Table for job queue management
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,   -- "queued", "processing", "completed", "failed"
                rss_url TEXT NOT NULL,
                num_episodes INTEGER,
                sample_duration INTEGER,
                output_data TEXT,       -- Store JSON string of transcription results
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            conn.commit()
            print(f"SQLite database tables initialized at: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Error initializing database tables: {e}")
            conn.rollback()
        finally:
            conn.close()

    def save_transcript(self, title, transcript):
        """
        Saves the episode title and its transcribed text to the 'podcast_transcripts' table.
        Uses INSERT OR REPLACE to update if title exists, or insert if new.

        Args:
            title (str): The title of the podcast episode.
            transcript (str): The transcribed text of the episode.
        """
        if not title or not transcript:
            print("Title or transcript is empty, skipping database save.")
            return

        conn = self._get_connection()
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
        Retrieves all episode records (title, transcript) from the 'podcast_transcripts' table.

        Returns:
            list: A list of dictionaries, where each dictionary represents a record
                  with keys 'objectID', 'title', and 'transcription', suitable for Algolia.
        """
        conn = self._get_connection()
        records = []
        try:
            conn.row_factory = sqlite3.Row # This allows us to fetch rows as dictionaries
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

    # Methods for Job Queue Management

    def add_job(self, job_id: str, rss_url: str, num_episodes: int, sample_duration: int):
        """
        Adds a new job to the 'jobs' table with 'queued' status.

        Args:
            job_id (str): The unique ID generated by RQ for the job.
            rss_url (str): The RSS feed URL for the job.
            num_episodes (int): Number of episodes to process for this job.
            sample_duration (int): Duration of audio sample for this job.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO jobs (job_id, status, rss_url, num_episodes, sample_duration)
                VALUES (?, ?, ?, ?, ?)
            ''', (job_id, "queued", rss_url, num_episodes, sample_duration))
            conn.commit()
            print(f"Job {job_id} added to DB with status 'queued'.")
        except sqlite3.Error as e:
            print(f"Error adding job {job_id} to database: {e}")
            conn.rollback()
        finally:
            conn.close()

    def update_job_status(self, job_id: str, status: str, output_data: str = None, error_message: str = None):
        """
        Updates the status of a job in the 'jobs' table.

        Args:
            job_id (str): The unique ID of the job.
            status (str): The new status ("processing", "completed", "failed").
            output_data (str, optional): JSON string of results for completed jobs.
            error_message (str, optional): Error details for failed jobs.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE jobs
                SET status = ?, output_data = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
            ''', (status, output_data, error_message, job_id))
            conn.commit()
            print(f"Job {job_id} status updated to '{status}'.")
        except sqlite3.Error as e:
            print(f"Error updating job {job_id} status: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_job_details(self, job_id: str):
        """
        Retrieves details for a specific job from the 'jobs' table.

        Args:
            job_id (str): The unique ID of the job.

        Returns:
            dict or None: A dictionary containing job details, or None if not found.
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row # Allows accessing columns by name
        job_details = None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                job_details = dict(row) # Convert Row object to dictionary
        except sqlite3.Error as e:
            print(f"Error retrieving job {job_id} details: {e}")
        finally:
            conn.close()
        return job_details

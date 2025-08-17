# Standard library imports
import os
import asyncio
from datetime import datetime
import gc
import traceback

# Local module imports
from fetch_rss import RSSFetcher
from download_audio import AudioDownloader
from transcribe import Transcriber
from database import DatabaseManager
from upload_algolia import AlgoliaUploader

class PodcastWorkflow:
    """
    Orchestrates the entire podcast transcription and indexing workflow.
    Manages fetching, downloading, transcribing, storing, and uploading data.
    This class is now a standalone module.
    """

    def __init__(self, algolia_app_id=None, algolia_api_key=None, db_path="podcast_transcripts.db"):
        """
        Initializes the workflow components.
        API keys are now passed dynamically per run or initialized to None.

        Args:
            algolia_app_id (str, optional): User's Algolia Application ID. Defaults to None.
            algolia_api_key (str, optional): User's Algolia Write API Key. Defaults to None.
            db_path (str, optional): Path to the SQLite database file. Defaults to "podcast_transcripts.db".
        """
        self.rss_fetcher = RSSFetcher()
        self.audio_downloader = AudioDownloader()
        # self.transcriber is NO LONGER initialized here.
        # It will be initialized inside run_workflow with the user-provided key.
        self.db_manager = DatabaseManager(db_path=db_path)
        
        self.algolia_uploader = None
        # Initialize Algolia uploader with provided credentials
        if algolia_app_id and algolia_api_key:
            try:
                self.algolia_uploader = AlgoliaUploader(algolia_app_id, algolia_api_key)
            except ValueError as e:
                print(f"Algolia Uploader initialization failed: {e}")
                self.algolia_uploader = None
        
        self.status_messages = []

    def _log_status(self, message):
        """Helper to append messages to the status list and print them."""
        self.status_messages.append(f"{datetime.now().strftime('%H:%M:%S')} - {message}")
        print(message)

    async def run_workflow(self, rss_url, num_episodes=1, sample_duration=60, openai_api_key=None):
        """
        Executes the full podcast transcription and indexing workflow.

        Args:
            rss_url (str): The URL of the podcast's RSS feed.
            num_episodes (int): The number of episodes to transcribe.
            sample_duration (int): The duration in seconds for each audio sample.
            openai_api_key (str): User-provided OpenAI API Key.
        """
        self.status_messages = []
        self._log_status("Starting podcast transcription workflow...")

        # Clear the database at the start of each run
        self._log_status("Clearing existing podcast transcripts from the database...")
        self.db_manager.clear_all_transcripts()
        
        # Initialize Transcriber here with the user-provided key
        # This ensures the OpenAI client is only created when the key is available
        transcriber_instance = Transcriber(openai_api_key=openai_api_key)

        self._log_status(f"Fetching {num_episodes} episodes from RSS feed: {rss_url}...")
        episodes = self.rss_fetcher.parse_feed(rss_url, max_episodes=num_episodes)
        self._log_status(f"Found {len(episodes)} episodes with audio URLs.")

        if not episodes:
            self._log_status("No episodes with audio found to process.")
            return {"message": "No episodes with audio found in the feed.", "status_updates": self.status_messages}, 200

        transcribed_episodes_info = []

        for i, ep in enumerate(episodes):
            self._log_status(f"\n--- Processing episode {i+1}/{len(episodes)}: {ep['title']} ---")
            
            sample_path = None
            try:
                self._log_status(f"Downloading {sample_duration}s audio sample for '{ep['title']}'...")
                sample_path = self.audio_downloader.download_random_sample(ep["audio_url"], duration_sec=sample_duration)

                if sample_path:
                    self._log_status(f"Sample saved to: {sample_path}")
                    
                    self._log_status(f"Transcribing audio sample for '{ep['title']}'...")
                    # Use the newly created transcriber_instance
                    transcription = transcriber_instance.transcribe_audio(sample_path)
                    
                    if "Error" in transcription:
                        self._log_status(f"Transcription failed for '{ep['title']}': {transcription}")
                        return {"error": transcription, "status_updates": self.status_messages}, 500
                    
                    if transcription:
                        self._log_status(f"Transcription complete for '{ep['title']}'.")
                        podcast_entry = {
                            "title": ep["title"],
                            "published": ep.get("published", datetime.now().isoformat()),
                            "audio_url": ep["audio_url"],
                            "transcription": transcription,
                            "processed_date": datetime.now().isoformat()
                        }

                        self._log_status(f"Saving '{podcast_entry['title']}' to database...")
                        self.db_manager.save_transcript(podcast_entry["title"], podcast_entry["transcription"]) 
                        self._log_status(f"Saved '{podcast_entry['title']}' to database.")

                        # UPLOAD TO ALGOLIA IMMEDIATELY AFTER PROCESSING EACH EPISODE
                        if self.algolia_uploader:
                            self._log_status(f"Uploading transcription for '{podcast_entry['title']}' to Algolia...")
                            algolia_record = {
                                "objectID": podcast_entry["audio_url"],
                                "title": podcast_entry["title"],
                                "transcription": podcast_entry["transcription"]
                            }
                            # Upload a list containing just this single record
                            await self.algolia_uploader.upload_transcripts([algolia_record]) 
                            self._log_status(f"Uploaded '{podcast_entry['title']}' to Algolia.")
                        else:
                            self._log_status("Algolia Uploader not initialized. Skipping Algolia upload for this episode.")

                        transcribed_episodes_info.append({
                            "title": podcast_entry["title"],
                            "transcription_preview": transcription[:200] + "..." if len(transcription) > 200 else transcription,
                            "full_transcription": transcription
                        })
                    else:
                        self._log_status(f"No transcript generated for '{ep['title']}'.")

                else:
                    self._log_status(f"Skipping transcription for '{ep['title']}' due to download/processing error.")

            except Exception as e:
                self._log_status(f"An unexpected error occurred during processing '{ep['title']}': {e}")
                traceback.print_exc()
                return {"error": f"An unexpected error occurred during episode processing: {e}", "status_updates": self.status_messages}, 500
            finally:
                if sample_path and os.path.exists(sample_path):
                    os.remove(sample_path)
                    self._log_status(f"Cleaned up sample audio file (workflow level): {sample_path}")
                gc.collect()

        # This section will only log if Algolia wasn't initialized at all or no new episodes were transcribed.
        if not self.algolia_uploader:
            self._log_status("\nAlgolia Uploader not initialized. No records were uploaded to Algolia during this run.")
        elif not transcribed_episodes_info: # If algolia_uploader exists but no episodes were transcribed successfully
            self._log_status("\nNo episodes were successfully transcribed to upload to Algolia.")

        self._log_status("\nPodcast transcription workflow completed.")

        return {
            "message": "Podcast transcription workflow completed successfully!",
            "transcribed_episodes": transcribed_episodes_info,
            "algolia_app_id": self.algolia_uploader.algolia_app_id if self.algolia_uploader else None,
            "algolia_index": self.algolia_uploader.algolia_index if self.algolia_uploader else None,
            "status_updates": self.status_messages
        }, 200

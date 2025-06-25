# Standard library imports
import os
import asyncio
from datetime import datetime # Added for processed_date in database entry
import gc # For garbage collection

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

    def __init__(self, rss_url, algolia_app_id=None, algolia_api_key=None, db_path="podcast_transcripts.db"):
        """
        Initializes the workflow components.

        Args:
            rss_url (str): The URL of the podcast's RSS feed.
            algolia_app_id (str, optional): Your Algolia Application ID. Defaults to None.
            algolia_api_key (str, optional): Your Algolia Write API Key. Defaults to None.
            db_path (str, optional): Path to the SQLite database file. Defaults to "podcast_transcripts.db".
        """
        self.rss_url = rss_url
        self.rss_fetcher = RSSFetcher()
        self.audio_downloader = AudioDownloader()
        self.transcriber = Transcriber()
        self.db_manager = DatabaseManager(db_path=db_path)
        
        self.algolia_uploader = None
        # Initialize Algolia uploader only if credentials are provided
        if algolia_app_id and algolia_api_key:
            try:
                self.algolia_uploader = AlgoliaUploader(algolia_app_id, algolia_api_key)
            except ValueError as e:
                print(f"Algolia Uploader initialization failed: {e}")
                self.algolia_uploader = None # Ensure it's None if init failed

    async def run_workflow(self):
        """
        Executes the full podcast transcription and indexing workflow.
        """
        print("Starting podcast transcription workflow...")
        
        # 1. Fetch episodes from RSS feed
        episodes = self.rss_fetcher.parse_feed(self.rss_url)
        print(f"Found {len(episodes)} episodes with audio URLs.")

        # --- IMPORTANT CHANGE: Process ONLY THE FIRST EPISODE for now ---
        # This reduces the memory pressure by not looping through multiple episodes in one request.
        if not episodes:
            print("No episodes with audio found to process.")
            return {"message": "No episodes with audio found in the feed."}, 200 # Return specific message

        # Take only the first episode for processing in this request
        episode_to_process = episodes[0] 
        print(f"\n--- Processing episode 1/1: {episode_to_process['title']} ---")
        
        sample_path = None # Initialize outside try for finally block access
        try:
            # Download a random sample of the episode's audio
            sample_path = self.audio_downloader.download_random_sample(episode_to_process["audio_url"])

            if sample_path:
                print(f"Sample saved to: {sample_path}")
                
                # Transcribe the audio sample
                transcription = self.transcriber.transcribe_audio(sample_path)
                
                if "Error" in transcription: # Check for the 'Error' prefix in the string from Transcriber
                    print(f"Transcription failed for '{episode_to_process['title']}': {transcription}")
                    return {"error": transcription}, 500 # Return specific error
                
                if transcription:
                    print(f"Transcript (first 200 chars) for '{episode_to_process['title']}':")
                    print(transcription[:200] + "...")
                    
                    # Prepare data for the database and Algolia
                    podcast_entry = {
                        "title": episode_to_process["title"],
                        "published": episode_to_process.get("published", datetime.now().isoformat()), # Assuming 'published' might be missing in some RSS feeds
                        "audio_url": episode_to_process["audio_url"],
                        "transcription": transcription,
                        "processed_date": datetime.now().isoformat()
                    }

                    # Save to local SQLite DB
                    self.db_manager.save_transcript(podcast_entry["title"], podcast_entry["transcription"]) 
                    print(f"Saved '{podcast_entry['title']}' to database.")

                    # Upload to Algolia (only this episode for now)
                    if self.algolia_uploader:
                        algolia_record = {
                            "objectID": podcast_entry["audio_url"], # Unique ID for Algolia
                            "title": podcast_entry["title"],
                            "transcription": podcast_entry["transcription"]
                        }
                        # AlgoliaUploader expects a list of records
                        await self.algolia_uploader.upload_transcripts([algolia_record]) 
                        print(f"Uploaded '{podcast_entry['title']}' to Algolia (lean record).")
                    else:
                        print("Algolia Uploader not initialized. Skipping Algolia upload for this episode.")

                    return {
                        "message": "Podcast episode processed successfully!",
                        "episode_title": episode_to_process["title"],
                        "transcription": transcription, # Return full transcription for frontend
                        "transcription_preview": transcription[:200] + "..." if len(transcription) > 200 else transcription,
                    }, 200 # Return success and data
                else:
                    print(f"No transcript generated for '{episode_to_process['title']}'.")
                    return {"message": f"Transcription process completed, but no transcript generated for '{episode_to_process['title']}'."}, 200

            else:
                print(f"Skipping transcription for '{episode_to_process['title']}' due to download/processing error.")
                return {"error": f"Failed to download/process audio sample for '{episode_to_process['title']}'."}, 500

        except Exception as e:
            print(f"An unexpected error occurred in run_workflow: {e}")
            return {"error": f"An unexpected error occurred: {e}"}, 500
        finally:
            # Clean up the temporary audio sample file if it was created and still exists.
            # The download_random_sample already handles this, but keep as a fallback.
            if sample_path and os.path.exists(sample_path):
                os.remove(sample_path)
                print(f"Cleaned up sample file (workflow level): {sample_path}")


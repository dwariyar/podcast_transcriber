# Standard library imports
import os
import asyncio

# Third-party library imports
from dotenv import load_dotenv

# Local module imports
from fetch_rss import RSSFetcher
from download_audio import AudioDownloader
from transcribe import Transcriber
from database import DatabaseManager
from upload_algolia import AlgoliaUploader

# Load environment variables from the .env file.
load_dotenv()

class PodcastWorkflow:
    """
    Orchestrates the entire podcast transcription and indexing workflow.
    Manages fetching, downloading, transcribing, storing, and uploading data.
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
        self.rss_url = rss_url # Added: Store rss_url as an instance attribute
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
        episodes = self.rss_fetcher.parse_feed(self.rss_url) # Access self.rss_url now
        print(f"Found {len(episodes)} episodes with audio URLs.")

        # 2. Process each episode
        for i, ep in enumerate(episodes):
            print(f"\n--- Processing episode {i+1}/{len(episodes)}: {ep['title']} ---")
            
            # Download a random sample of the episode's audio
            sample_path = self.audio_downloader.download_random_sample(ep["audio_url"])

            if sample_path:
                print(f"Sample saved to: {sample_path}")
                
                # Transcribe the audio sample
                transcript = self.transcriber.transcribe_audio(sample_path)
                
                if transcript:
                    print(f"Transcript (first 200 chars) for '{ep['title']}':")
                    print(transcript[:200] + "...")
                    # Save to local SQLite DB
                    self.db_manager.save_transcript(ep["title"], transcript) 
                else:
                    print(f"No transcript generated for '{ep['title']}'.")
                
                # Clean up the temporary audio sample file after processing
                os.remove(sample_path)
                print(f"Cleaned up sample audio file: {sample_path}")
            else:
                print(f"Skipping transcription for '{ep['title']}' due to download/processing error.")

        # 3. Upload all processed data to Algolia
        if self.algolia_uploader:
            print("\n--- Uploading all processed data to Algolia ---")
            # Fetch all records from DB to ensure all are uploaded
            all_records = self.db_manager.fetch_all_transcripts() 
            await self.algolia_uploader.upload_transcripts(all_records)
        else:
            print("\nAlgolia Uploader not initialized. Skipping Algolia upload.")

        print("\nPodcast transcription workflow completed.")


if __name__ == "__main__":
    # Prompt the user for the podcast RSS feed URL
    RSS_URL = input("Enter podcast RSS feed URL: ").strip()

    # Retrieve Algolia credentials from environment variables loaded from .env
    ALGOLIA_APP_ID = os.getenv("APP_ID")
    ALGOLIA_WRITE_API_KEY = os.getenv("ALGOLIA_WRITE_API_KEY")

    # Conditional execution based on RSS URL and Algolia credentials availability
    if not RSS_URL:
        print("RSS feed URL cannot be empty. Exiting.")
    else:
        # Initialize the main workflow class
        workflow = PodcastWorkflow(RSS_URL, ALGOLIA_APP_ID, ALGOLIA_WRITE_API_KEY)
        # Run the asynchronous workflow
        asyncio.run(workflow.run_workflow())


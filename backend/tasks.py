# tasks.py
import asyncio
import json
import os
import traceback

from rq import Queue
from redis import Redis

# Local module imports
from podcast_workflow import PodcastWorkflow
from database import DatabaseManager

# Connect to Redis
# For DigitalOcean deployment, this needs to be configured to your Redis instance.
# For local testing, 'localhost' is fine if you have Redis installed.
redis_conn = Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", 6379)), db=0)
queue = Queue(connection=redis_conn)

def run_ingestion(
    job_id: str, # Pass job_id to the worker for status updates
    rss_url: str,
    num_episodes: int,
    sample_duration: int,
    openai_api_key: str,
    algolia_app_id: str,
    algolia_write_api_key: str,
    algolia_index_name: str
):
    """
    This function is executed by the RQ worker in the background.
    It orchestrates the podcast transcription workflow.
    """
    db_manager = DatabaseManager(db_path="podcast_transcripts.db")
    
    # Update job status to 'processing'
    db_manager.update_job_status(job_id, "processing")
    
    workflow_instance = None # Initialize to None for finally block
    try:
        # Initialize PodcastWorkflow with all required keys
        workflow_instance = PodcastWorkflow(
            algolia_app_id=algolia_app_id,
            algolia_api_key=algolia_write_api_key,
            algolia_index=algolia_index_name,
            db_path="podcast_transcripts.db"
        )
        
        # Execute the asynchronous workflow
        # asyncio.run is used here to run the async run_workflow in a sync context (RQ worker)
        response_data, status_code = asyncio.run(workflow_instance.run_workflow(
            rss_url=rss_url,
            num_episodes=num_episodes,
            sample_duration=sample_duration,
            openai_api_key=openai_api_key # Pass OpenAI key to workflow
        ))
        
        if status_code == 200:
            # If successful, store a subset of useful output data
            output_json = json.dumps(response_data.get("transcribed_episodes", []))
            db_manager.update_job_status(job_id, "completed", output_data=output_json)
        else:
            # If workflow returned an error status
            error_msg = response_data.get("error", "Unknown error during workflow execution.")
            db_manager.update_job_status(job_id, "failed", error_message=error_msg)

    except Exception as e:
        # Catch any unexpected errors during job execution
        error_msg = f"An unhandled error occurred in worker: {e}\n{traceback.format_exc()}"
        print(error_msg) # Print to worker logs
        db_manager.update_job_status(job_id, "failed", error_message=error_msg)
    finally:
        # Ensure cleanup even if errors occur
        if workflow_instance and hasattr(workflow_instance, 'status_messages'):
            pass
        print(f"Worker finished processing job {job_id}.")

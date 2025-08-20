# Standard library imports
import os
import asyncio
import json
import logging
import sys

# Third-party library imports
from quart import Quart, request, jsonify
from quart_cors import cors # Using quart_cors for Quart
from dotenv import load_dotenv

# Local module imports
# Ensure these imports are correct based on your project structure.
# Assuming tasks.py is in the same directory as app.py
from tasks import queue, run_ingestion
from database import DatabaseManager # Import DatabaseManager to query job status

# Load environment variables from the .env file
load_dotenv()

# Initialize Quart app with CORS
app = Quart(__name__)
app = cors(app, allow_origin=[
    "https://dwariyar.github.io/podcast_transcriber/",
    "http://localhost:3000",
    "https://podcast-transcriber-4x8ka.ondigitalocean.app/"
])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
    stream=sys.stdout  # Ensures logs go to stdout for Docker/DigitalOcean
)

# Initialize DatabaseManager for the main app to interact with job statuses
db_manager = DatabaseManager(db_path="podcast_transcripts.db")

# Health check endpoint for DigitalOcean
@app.route("/")
async def health():
    return jsonify({"status": "running"}), 200

# Endpoint to submit a new transcription job
@app.route('/transcribe', methods=['POST'])
async def submit_transcription_job():
    logging.info("Received request to /transcribe endpoint to submit a job.")

    data = await request.get_json()
    if not data or 'rss_url' not in data:
        logging.warning("Invalid request: 'rss_url' missing from JSON payload.")
        return jsonify({"error": "Missing 'rss_url' in request"}), 400

    # Extract parameters from request payload
    rss_url_from_frontend = data['rss_url']
    num_episodes = data.get('numEpisodes', 1)
    sample_duration = data.get('sampleDuration', 60)
    
    # Extract user-provided API keys
    openai_api_key = data.get('openaiApiKey')
    algolia_app_id = data.get('algoliaAppId')
    algolia_write_api_key = data.get('algoliaWriteApiKey')

    # Validate API keys
    if not openai_api_key or not algolia_app_id or not algolia_write_api_key:
        logging.warning("Missing one or more required inputs in request payload.")
        return jsonify({"error": "Missing one or more required inputs in request payload."}), 400

    logging.info(f"Submitting job for RSS URL: {rss_url_from_frontend}, Episodes: {num_episodes}, Sample Duration: {sample_duration}s")

    try:
        # Enqueue the job to RQ
        # Pass all necessary parameters directly to the worker function
        job = queue.enqueue(
            run_ingestion,
            job_id=None, # RQ will generate a UUID if None
            rss_url=rss_url_from_frontend,
            num_episodes=num_episodes,
            sample_duration=sample_duration,
            openai_api_key=openai_api_key,
            algolia_app_id=algolia_app_id,
            algolia_write_api_key=algolia_write_api_key,
            job_timeout=900 # Set a generous timeout for the RQ job (e.g., 15 minutes)
        )
        
        # Store initial job status in SQLite for easier querying by job_id
        db_manager.add_job(
            job_id=job.get_id(),
            rss_url=rss_url_from_frontend,
            num_episodes=num_episodes,
            sample_duration=sample_duration
        )

        return jsonify({"message": "Transcription job submitted successfully!", "job_id": job.get_id(), "status": "queued"}), 202 # 202 Accepted

    except Exception as e:
        logging.error(f"An error occurred while submitting job: {e}")
        return jsonify({"error": f"Failed to submit transcription job: {e}"}), 500

# Endpoint to check job status
@app.route("/status/<job_id>", methods=['GET'])
async def get_job_status(job_id):
    logging.info(f"Received request for job status: {job_id}")
    
    # Try to get job details from SQLite first
    job_details = db_manager.get_job_details(job_id)

    if not job_details:
        # If not found in SQLite, try to fetch from Redis (RQ)
        # This is a fallback and can be slow if Redis is not configured or job is very old
        try:
            job = queue.fetch_job(job_id)
            if job:
                job_details = {
                    "job_id": job.get_id(),
                    "status": job.get_status(), # RQ job status (queued, started, finished, failed)
                    "result": job.result, # Result stored by RQ (if any)
                    "exc_info": job.exc_info # Exception info if job failed
                }
            else:
                return jsonify({"error": "Job not found."}), 404
        except Exception as e:
            logging.error(f"Error fetching job {job_id} from RQ/Redis: {e}")
            return jsonify({"error": "Error fetching job status."}), 500

    # For 'completed' jobs, parse the output_data
    if job_details and job_details.get("status") == "completed" and job_details.get("output_data"):
        try:
            job_details["transcribed_episodes"] = json.loads(job_details["output_data"])
            del job_details["output_data"] # Remove raw JSON string
        except json.JSONDecodeError:
            logging.error(f"Failed to decode output_data for job {job_id}")
            job_details["transcribed_episodes"] = [] # Clear or handle corrupted data

    return jsonify(job_details), 200

# Startup and shutdown hooks for Quart (optional, mainly for graceful shutdowns)
@app.before_serving
async def startup():
    logging.info("Quart app starting up...")
    # Ensure database tables are created on startup
    db_manager._create_tables()

@app.after_serving
async def shutdown():
    logging.info("Quart app shutting down...")
    # Clean up resources if necessary (e.g., close DB connections)

if __name__ == '__main__':
    # When running locally, ensure Redis is running (e.g., `redis-server`)
    logging.info("Starting Flask app locally...")
    app.run(host='0.0.0.0', port=os.getenv("PORT", 5001), debug=True)

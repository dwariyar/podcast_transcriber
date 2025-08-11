# Standard library imports
import os
import asyncio
import json

# Third-party library imports
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Local module imports from backend
from podcast_workflow import PodcastWorkflow

# Load environment variables from the .env file.
# We'll still load it for PORT, but API keys will come from frontend
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure CORS (Cross-Origin Resource Sharing)
CORS(app, 
     origins=["https://dwariyar.github.io/", "http://localhost:3000", "https://podcast-transcriber-4x8ka.ondigitalocean.app/"],
     methods=["GET", "POST", "OPTIONS", "PUT", "DELETE", "PATCH"],
     allow_headers=["Content-Type", "Authorization", "*"],
     supports_credentials=True
)

# RSS_URL_PLACEHOLDER is still here for initial workflow instance creation
RSS_URL_PLACEHOLDER = "https://feeds.npr.org/510310/podcast.xml"

# This instance will handle all transcription/indexing.
# It will be re-initialized with user-provided keys per request.
# For now, initialize with None for keys as they will be passed dynamically.
podcast_workflow_instance = PodcastWorkflow(
    algolia_app_id=None, # Will be passed dynamically
    algolia_api_key=None, # Will be passed dynamically
    db_path="podcast_transcripts.db"
)

@app.route('/transcribe', methods=['POST'])
async def transcribe_podcast():
    """
    API endpoint to receive an RSS feed URL, transcription parameters,
    and user-provided API keys to trigger podcast transcription.
    """
    print("Received request to /transcribe endpoint.")
    
    data = request.get_json()
    if not data or 'rss_url' not in data:
        print("Invalid request: 'rss_url' missing from JSON payload.")
        return jsonify({"error": "Missing 'rss_url' in request"}), 400

    # Extract all parameters from the request payload
    rss_url_from_frontend = data['rss_url']
    num_episodes = data.get('numEpisodes', 1)
    sample_duration = data.get('sampleDuration', 60)
    
    # Extract user-provided API keys
    openai_api_key = data.get('openaiApiKey')
    algolia_app_id = data.get('algoliaAppId')
    algolia_write_api_key = data.get('algoliaWriteApiKey')

    # Basic validation for keys
    if not openai_api_key or not algolia_app_id or not algolia_write_api_key:
        return jsonify({"error": "Missing one or more API keys in request payload."}), 400

    print(f"Transcription request for RSS URL: {rss_url_from_frontend}, Episodes: {num_episodes}, Sample Duration: {sample_duration}s")

    try:
        # Re-initialize the workflow instance with user-provided keys for this request
        # This ensures each request uses the specific keys provided by the user
        current_workflow_instance = PodcastWorkflow(
            algolia_app_id=algolia_app_id,
            algolia_api_key=algolia_write_api_key,
            db_path="podcast_transcripts.db" # Still use the default DB path
        )
        # Pass the OpenAI key to the workflow's run_workflow method
        response_data, status_code = await current_workflow_instance.run_workflow(
            rss_url=rss_url_from_frontend,
            num_episodes=num_episodes,
            sample_duration=sample_duration,
            openai_api_key=openai_api_key # Pass OpenAI key
        )
        
        return jsonify(response_data), status_code

    except ValueError as e:
        print(f"Workflow configuration error: {e}")
        # Ensure status_messages are returned even on error
        return jsonify({"error": str(e), "status_updates": podcast_workflow_instance.status_messages}), 500
    except Exception as e:
        print(f"An error occurred during workflow execution: {e}")
        # Ensure status_messages are returned even on error
        return jsonify({"error": "Transcription failed due to an internal server error.", "status_updates": podcast_workflow_instance.status_messages}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv("PORT", 5001), debug=True)

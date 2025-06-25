# Standard library imports
import os
import asyncio
import json # To work with JSON data for API responses

# Third-party library imports
from flask import Flask, request, jsonify # Flask for web application, request for handling incoming data, jsonify for sending JSON responses
from flask_cors import CORS # Flask-CORS for handling Cross-Origin Resource Sharing
from dotenv import load_dotenv # For loading environment variables from a .env file

# Local module imports from your backend
from podcast_workflow import PodcastWorkflow # Import PodcastWorkflow from its dedicated file

# Load environment variables from the .env file.
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure CORS (Cross-Origin Resource Sharing)
CORS(app, origins="https://dwariyar.github.io/")

# --- Retrieve Algolia Credentials ---
ALGOLIA_APP_ID = os.getenv("APP_ID") # Updated to use "APP_ID"
ALGOLIA_WRITE_API_KEY = os.getenv("ALGOLIA_WRITE_API_KEY")
RSS_URL_PLACEHOLDER = "https://feeds.npr.org/510310/podcast.xml" # Dummy URL for initial workflow instance

# This instance will handle all transcription/indexing.
podcast_workflow_instance = PodcastWorkflow(
    rss_url=RSS_URL_PLACEHOLDER, # This will be overwritten by request.json['rss_url']
    algolia_app_id=ALGOLIA_APP_ID,
    algolia_api_key=ALGOLIA_WRITE_API_KEY,
    db_path="podcast_transcripts.db"
)

@app.route('/transcribe', methods=['POST'])
async def transcribe_podcast():
    """
    API endpoint to receive an RSS feed URL and trigger podcast transcription.
    Expects a JSON payload with an 'rss_url' key.
    """
    print("Received request to /transcribe endpoint.")
    
    data = request.get_json()
    if not data or 'rss_url' not in data:
        print("Invalid request: 'rss_url' missing from JSON payload.")
        return jsonify({"error": "Missing 'rss_url' in request"}), 400

    rss_url_from_frontend = data['rss_url']
    print(f"Transcription request for RSS URL: {rss_url_from_frontend}")

    # Update the workflow instance's RSS URL for the current request
    podcast_workflow_instance.rss_url = rss_url_from_frontend
    
    try:
        # Call run_workflow which now returns a (response_data, status_code) tuple
        response_data, status_code = await podcast_workflow_instance.run_workflow()
        
        return jsonify(response_data), status_code

    except ValueError as e:
        print(f"Workflow configuration error: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"An error occurred during workflow execution: {e}")
        return jsonify({"error": "Transcription failed due to an internal server error."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv("PORT", 5000), debug=True) # Use os.getenv for port

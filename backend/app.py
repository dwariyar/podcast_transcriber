# Standard library imports
import os
import asyncio
import json # To work with JSON data for API responses

# Third-party library imports
from flask import Flask, request, jsonify # Flask for web application, request for handling incoming data, jsonify for sending JSON responses
from flask_cors import CORS # Flask-CORS for handling Cross-Origin Resource Sharing
from dotenv import load_dotenv # For loading environment variables from a .env file

# Local module imports from your backend
from podcast_workflow import PodcastWorkflow # Changed import path

# Load environment variables from the .env file.
# This ensures API keys and other configurations are available to Flask.
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure CORS (Cross-Origin Resource Sharing)
# For production, you should replace "*" with the actual domain of your frontend (e.g., "https://yourfrontend.com").
CORS(app) # Allows all origins for development ease

# --- Retrieve Algolia Credentials ---
# Use the APP_ID from your .env file
ALGOLIA_APP_ID = os.getenv("APP_ID")
ALGOLIA_WRITE_API_KEY = os.getenv("ALGOLIA_WRITE_API_KEY")
RSS_URL_PLACEHOLDER = "https://feeds.npr.org/510310/podcast.xml" # A placeholder/default RSS URL if needed for testing

# This will hold the instance of your PodcastWorkflow.
# We initialize it here so the Whisper model only loads once when the Flask app starts.
# We pass a placeholder RSS_URL because the actual one comes from the API request.
# The db_path ensures a consistent database location.
podcast_workflow_instance = PodcastWorkflow(
    rss_url=RSS_URL_PLACEHOLDER, # This is a dummy for initialization, actual RSS comes from request
    algolia_app_id=ALGOLIA_APP_ID,
    algolia_api_key=ALGOLIA_WRITE_API_KEY,
    db_path="podcast_transcripts.db" # Ensure this matches what your database.py uses
)

@app.route('/transcribe', methods=['POST'])
async def transcribe_podcast():
    """
    API endpoint to receive an RSS feed URL and trigger podcast transcription.
    Expects a JSON payload with an 'rss_url' key.
    """
    print("Received request to /transcribe endpoint.")
    
    # 1. Parse incoming JSON request
    data = request.get_json()
    if not data or 'rss_url' not in data:
        print("Invalid request: 'rss_url' missing from JSON payload.")
        return jsonify({"error": "Missing 'rss_url' in request"}), 400

    rss_url_from_frontend = data['rss_url']
    print(f"Transcription request for RSS URL: {rss_url_from_frontend}")

    # 2. Update the workflow instance's RSS URL and run the transcription
    podcast_workflow_instance.rss_url = rss_url_from_frontend
    
    try:
        # Run the asynchronous workflow.
        # This will execute the entire process: fetch, download, transcribe, save, upload.
        await podcast_workflow_instance.run_workflow()

        # For a simple API response, we'll indicate success.
        # You could also fetch the *latest* transcript from your DB here if needed.
        # To get the transcript that was just processed (assuming it's the latest one for simplicity)
        # You might need a more sophisticated way to retrieve specific transcripts if processing multiple.
        latest_transcript_record = None
        all_transcripts = podcast_workflow_instance.db_manager.fetch_all_transcripts()
        if all_transcripts:
            # Assuming the last added transcript is the one we just processed.
            # In a real app, you might want to link the task ID to the DB entry,
            # or pass the ID of the newly saved record.
            latest_transcript_record = all_transcripts[-1] 
            latest_transcript_text = latest_transcript_record[2] # transcript is at index 2

            # If the process was successful, the transcript should be in the DB.
            return jsonify({
                "status": "success",
                "message": "Podcast transcription and indexing initiated successfully.",
                "transcript": latest_transcript_text
            }), 200
        else:
            return jsonify({
                "status": "success",
                "message": "Podcast transcription initiated, but no transcripts found to return."
            }), 200

    except ValueError as e:
        # Catch specific errors like Algolia credential issues
        print(f"Workflow configuration error: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"An error occurred during workflow execution: {e}")
        return jsonify({"error": "Transcription failed due to an internal server error."}), 500

# This block ensures the Flask development server runs when app.py is executed directly.
if __name__ == '__main__':
    # You can specify host and port. 0.0.0.0 makes it accessible from other devices on your network.
    # debug=True allows for automatic reloading on code changes and provides a debugger.
    app.run(host='0.0.0.0', port=5001, debug=True)


# Standard library imports
import os # For accessing environment variables

# Third-party library imports
from openai import OpenAI #Import the OpenAI client library
from dotenv import load_dotenv #For loading environment variables
load_dotenv() # Ensure env vars are loaded even if this file is run directly

class Transcriber:
    """
    A class to handle audio transcription using the OpenAI Commercial Whisper API.
    """

    def __init__(self):
        # Initialize the OpenAI client here.
        # This client will handle authentication using the API key.
        # The actual model is NOT loaded into this server's memory.
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            print("WARNING: OPENAI_API_KEY environment variable not set in Transcriber.__init__. OpenAI API calls will fail.")
        self.openai_client = OpenAI(api_key=self.openai_api_key)

    def transcribe_audio(self, audio_path):
        """
        Transcribes the given audio file using the OpenAI Commercial Whisper API.

        Args:
            audio_path (str): The file path to the audio sample to transcribe.
                              This file will be sent to the OpenAI API.

        Returns:
            str: The transcribed text, or an error string if transcription fails or input is invalid.
        """
        if not audio_path:
            print("No audio path provided for transcription, skipping.")
            return "Error: No audio path provided."
        
        if not self.openai_api_key:
            print("OpenAI API key not found. Cannot transcribe.")
            return "Error: OpenAI API key not configured."
        
        print(f"Transcribing audio with OpenAI Whisper API from: {audio_path} ...")
        try:
            # Open the temporary audio file in binary read mode
            # The OpenAI API expects a file-like object
            with open(audio_path, "rb") as audio_file:
                # Call the OpenAI Whisper API. 'whisper-1' is the model ID for the API.
                transcription = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            
            print("Transcription complete via OpenAI API.")
            return transcription.text # The transcribed text is in the 'text' attribute of the response object
        except Exception as e:
            print(f"Error during OpenAI Whisper API transcription of {audio_path}: {e}")
            return f"Error during transcription via OpenAI API: {e}"
# Standard library imports
import os
import traceback

# Third-party library imports
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

class Transcriber:
    """
    A class to handle audio transcription using the OpenAI Commercial Whisper API.
    """

    def __init__(self, openai_api_key): # Now requires openai_api_key as a direct argument
        # Initialize the OpenAI client with the provided API key.
        # No fallback to os.getenv as the key is expected to be provided by the user.
        self.openai_api_key = openai_api_key
        if not self.openai_api_key:
            # This warning should ideally not be hit if app.py validates the key
            print("WARNING: OpenAI API key not provided to Transcriber. OpenAI API calls will fail.")
        self.openai_client = OpenAI(api_key=self.openai_api_key)

    def transcribe_audio(self, audio_path):
        """
        Transcribes the given audio file using the OpenAI Commercial Whisper API.

        Args:
            audio_path (str): The file path to the audio sample to transcribe.

        Returns:
            str: The transcribed text, or an error string if transcription fails or input is invalid.
        """
        if not audio_path:
            print("No audio path provided for transcription, skipping.")
            return "Error: No audio path provided."
        
        if not self.openai_api_key:
            print("OpenAI API key not found or provided. Cannot transcribe.")
            return "Error: OpenAI API key not configured."
        
        print(f"Transcribing audio with OpenAI Whisper API from: {audio_path} ...")
        try:
            with open(audio_path, "rb") as audio_file:
                transcription = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            
            print("Transcription complete via OpenAI API.")
            return transcription.text
        except Exception as e:
            print(f"Error during OpenAI Whisper API transcription of {audio_path}: {e}")
            traceback.print_exc()
            return f"Error during transcription via OpenAI API: {e}"

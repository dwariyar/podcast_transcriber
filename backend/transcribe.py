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

    def __init__(self, openai_api_key): 
        self.openai_api_key = openai_api_key
        if not self.openai_api_key:
            print("WARNING: OpenAI API key not provided to Transcriber. OpenAI API calls will fail.")
        self.openai_client = OpenAI(api_key=self.openai_api_key)

    def transcribe_audio(self, audio_path):
        if not audio_path:
            print("No audio path provided for transcription, skipping.")
            return "Error: No audio path provided."
        
        if not self.openai_api_key:
            print("OpenAI API key not found or provided. Cannot transcribe.")
            return "Error: OpenAI API key not configured."
        
        print(f"Transcribing audio with OpenAI Whisper API from: {audio_path} ...")
        try:
            print("About to call OpenAI API...")
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
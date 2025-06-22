# Standard library imports
import requests   # For making HTTP requests, primarily to download audio files
import random     # For selecting a random sample of audio for transcription
import os         # For interacting with the operating system (e.g., file paths)
import tempfile   # For creating and managing temporary files and directories

# Third-party library imports
from pydub import AudioSegment # For audio manipulation (e.g., loading, slicing, exporting)

class AudioDownloader:
    """
    A class to download podcast audio files and extract random samples.
    """

    def download_random_sample(self, audio_url, duration_sec=60):
        """
        Downloads a portion of the audio from the given URL.
        If the audio is longer than `duration_sec`, a random `duration_sec` segment is taken.
        This helps reduce transcription time and resource usage for long podcasts.

        Args:
            audio_url (str): The URL of the audio file to download.
            duration_sec (int): The duration (in seconds) of the random sample to extract.

        Returns:
            str or None: The file path to the saved WAV audio sample, or None if download/processing fails.
        """
        if not audio_url:
            print("Audio URL is empty, skipping download.")
            return None

        print(f"Attempting to download audio from: {audio_url} ...")
        tmp_file_path = None
        sample_path = None
        try:
            # Create a temporary file to store the full downloaded audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                # Use requests.get with stream=True for large files
                response = requests.get(audio_url, stream=True)
                response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

                # Write content in chunks to avoid memory issues for large files
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk: # Filter out keep-alive new chunks
                        tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            print(f"Successfully downloaded full audio to temporary file: {tmp_file_path}")
            
            # Load the entire audio file using pydub
            audio = AudioSegment.from_file(tmp_file_path)
            total_ms = len(audio) # Total duration in milliseconds
            sample_ms = duration_sec * 1000 # Desired sample duration in milliseconds

            # Extract a random sample or the whole audio if it's shorter than the desired sample
            if total_ms <= sample_ms:
                sample = audio
                print(f"Audio is shorter than {duration_sec}s, using full audio for sample.")
            else:
                start_ms = random.randint(0, total_ms - sample_ms) # Random start point
                sample = audio[start_ms:start_ms + sample_ms]
                print(f"Extracted {duration_sec}s sample from {audio_url} (starting at {start_ms/1000:.2f}s).")
            
            # Export the sample to a WAV file, which is often preferred by transcription models
            sample_path = tmp_file_path.replace(".mp3", "_sample.wav") # Rename for clarity
            sample.export(sample_path, format="wav")
            print(f"Audio sample saved to: {sample_path}")
            
            return sample_path
        
        except requests.exceptions.RequestException as e:
            print(f"Error downloading audio from {audio_url}: {e}")
            return None
        except Exception as e:
            print(f"An error occurred during audio processing (pydub error, etc.): {e}")
            return None
        finally:
            # Ensure the initial full temporary audio file is removed
            if tmp_file_path and os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
                # print(f"Cleaned up full temporary audio file: {tmp_file_path}") # Verbose cleanup


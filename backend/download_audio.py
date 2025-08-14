# Standard library imports
import requests   # For making HTTP requests, primarily to download audio files
import random     # For selecting a random sample of audio for transcription
import os         # For interacting with the operating system (e.g., file paths)
import tempfile   # For creating and managing temporary files and directories
import gc         # Import garbage collector for explicit memory management
import traceback

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

        tmp_file_path = None
        sample_path = None
        audio_segment = None

        try:
            # Download full audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                response = requests.get(audio_url, stream=True)
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
                tmp_file_path = tmp_file.name

            print(f"Downloaded audio to temporary file: {tmp_file_path}")

            # Load audio with pydub, redirecting ffmpeg stderr to sys.stderr
            try:
                audio_segment = AudioSegment.from_file(
                    tmp_file_path, 
                    format="mp3",
                    ffmpeg_params=["-loglevel", "debug"]
                )
            except Exception as e:
                print(f"Error loading audio with pydub/ffmpeg: {e}")
                traceback.print_exc()
                return None

            total_ms = len(audio_segment)
            sample_ms = duration_sec * 1000
            if total_ms <= sample_ms:
                sample = audio_segment
            else:
                start_ms = random.randint(0, total_ms - sample_ms)
                sample = audio_segment[start_ms:start_ms + sample_ms]

            sample_path = tmp_file_path.replace(".mp3", "_sample.wav")
            try:
                sample.export(sample_path, format="wav")
            except Exception as e:
                print(f"Error exporting audio to WAV: {e}")
                traceback.print_exc()
                return None

            print(f"Audio sample saved to: {sample_path}")
            return sample_path
        finally:
            # Ensure the initial full temporary audio file is removed
            if tmp_file_path and os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
                print(f"Cleaned up full temporary audio file: {tmp_file_path}") # Added log

            # Explicitly delete the AudioSegment object and force garbage collection
            if audio_segment is not None:
                del audio_segment
                gc.collect() # Force garbage collection
                print("Explicitly released audio_segment and forced GC in AudioDownloader.")


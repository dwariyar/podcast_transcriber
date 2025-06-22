# Third-party library imports
import whisper # OpenAI's Whisper model for speech-to-text transcription

class Transcriber:
    """
    A class to handle audio transcription using OpenAI's Whisper model.
    """

    def __init__(self):
        self.whisper_model = None # Model is loaded lazily

    def load_whisper_model(self):
        """
        Loads the OpenAI Whisper ASR (Automatic Speech Recognition) model.
        The model is loaded only once to avoid repeated loading overhead.
        """
        if not self.whisper_model:
            print("Loading Whisper model (base)... This may take a moment.")
            # 'base' is a smaller, faster model; 'small', 'medium', 'large' offer higher accuracy.
            self.whisper_model = whisper.load_model("base")
            print("Whisper model loaded.")

    def transcribe_audio(self, audio_path):
        """
        Transcribes the given audio file using the loaded Whisper model.

        Args:
            audio_path (str): The file path to the audio sample to transcribe.

        Returns:
            str: The transcribed text, or an empty string if transcription fails or input is invalid.
        """
        if not audio_path:
            print("No audio path provided for transcription, skipping.")
            return ""
        
        self.load_whisper_model() # Ensure Whisper model is loaded
        
        print(f"Transcribing audio from: {audio_path} ...")
        try:
            # Perform the transcription
            result = self.whisper_model.transcribe(audio_path)
            transcript = result.get("text", "").strip()
            print("Transcription complete.")
            return transcript
        except Exception as e:
            print(f"Error during audio transcription of {audio_path}: {e}")
            return ""


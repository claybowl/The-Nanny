import whisper
from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv
from src.core.ai_services import AIServices

# Load environment variables
load_dotenv()

class WhisperSTT:
    def __init__(self, model_name: str = "base.en", use_api: bool = False):
        """Initialize Whisper STT handler.
        
        Args:
            model_name (str): Name of the Whisper model to use (for local model)
            use_api (bool): Whether to use OpenAI's Whisper API instead of local model
        """
        self.use_api = use_api
        if use_api:
            self.ai_services = AIServices()
        else:
            self.model = whisper.load_model(model_name)
    
    async def transcribe(self, audio_path: str | Path) -> Optional[str]:
        """Transcribe audio file to text.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Transcribed text or None if transcription fails
        """
        try:
            if self.use_api:
                return await self.ai_services.transcribe_audio_with_whisper_api(str(audio_path))
            else:
                result = self.model.transcribe(str(audio_path))
                return result["text"].strip()
        except Exception as e:
            print(f"Transcription error: {e}")
            return None 
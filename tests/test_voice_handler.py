import pytest
import tempfile
import wave
import numpy as np
from pathlib import Path
from src.voice.whisper_handler import WhisperSTT

@pytest.fixture
def temp_audio_file():
    """Create a temporary WAV file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        # Create a simple sine wave
        duration = 1  # seconds
        sample_rate = 16000
        samples = np.sin(2 * np.pi * 440 * np.linspace(0, duration, sample_rate))
        samples = (samples * 32767).astype(np.int16)
        
        with wave.open(tmp.name, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(samples.tobytes())
        
        yield Path(tmp.name)
        Path(tmp.name).unlink()

class TestWhisperSTT:
    def test_init(self):
        stt = WhisperSTT()
        assert stt.model is not None
    
    def test_transcribe_valid_audio(self, temp_audio_file):
        stt = WhisperSTT()
        result = stt.transcribe(temp_audio_file)
        assert result is not None
        assert isinstance(result, str)
    
    def test_transcribe_invalid_file(self):
        stt = WhisperSTT()
        result = stt.transcribe("nonexistent.wav")
        assert result is None 
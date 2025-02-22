import pytest
from fastapi.testclient import TestClient
import tempfile
import wave
import numpy as np
from pathlib import Path
from src.api.main import app

client = TestClient(app)

@pytest.fixture
def test_audio_file():
    """Create a test audio file."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        duration = 1
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

class TestAPIIntegration:
    def test_voice_endpoint(self, test_audio_file):
        with open(test_audio_file, 'rb') as f:
            response = client.post(
                "/voice/process-voice",
                files={"audio_file": ("test.wav", f, "audio/wav")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "transcribed_text" in data
        assert "command_result" in data
    
    def test_invalid_audio_format(self):
        with tempfile.NamedTemporaryFile(suffix='.txt') as tmp:
            tmp.write(b"not an audio file")
            tmp.seek(0)
            
            response = client.post(
                "/voice/process-voice",
                files={"audio_file": ("test.txt", tmp, "text/plain")}
            )
        
        assert response.status_code == 400 
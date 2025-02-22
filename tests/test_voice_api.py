import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import os

from src.api.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to CLAWD Agent API"}

def test_voice_endpoint_wrong_format():
    # Test with an unsupported file format
    files = {'audio_file': ('test.txt', b'some content', 'text/plain')}
    response = client.post("/voice/process-voice", files=files)
    assert response.status_code == 400

def create_test_audio():
    """Create a simple test audio file using sox (if available)"""
    try:
        import sox
        
        # Create a simple 1-second audio file
        transformer = sox.Transformer()
        transformer.synth(1, 'sine', 440)  # 1 second, 440 Hz sine wave
        
        test_file = "test_audio.wav"
        transformer.build_file(None, test_file)
        
        return test_file
    except ImportError:
        pytest.skip("sox not installed - skipping audio test")
        return None

def test_voice_endpoint_with_audio():
    test_file = create_test_audio()
    if not test_file:
        return
        
    try:
        with open(test_file, 'rb') as f:
            files = {'audio_file': ('test.wav', f, 'audio/wav')}
            response = client.post("/voice/process-voice", files=files)
            
        assert response.status_code == 200
        assert "status" in response.json()
        assert "command" in response.json()
        assert response.json()["status"] == "success"
    finally:
        if os.path.exists(test_file):
            os.remove(test_file) 
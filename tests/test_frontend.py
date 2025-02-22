import pytest
from src.frontend.app import AudioRecorder
import numpy as np
import av
import wave
import tempfile
from pathlib import Path

class MockFrame:
    def __init__(self, samples):
        self._samples = samples
    
    def to_ndarray(self, format=None):
        return self._samples

@pytest.fixture
def recorder():
    return AudioRecorder()

@pytest.fixture
def mock_audio_frame():
    # Create a mock audio frame with a sine wave
    duration = 0.1  # seconds
    sample_rate = 16000
    samples = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sample_rate * duration)))
    samples = (samples * 32767).astype(np.int16)
    return MockFrame(samples)

class TestAudioRecorder:
    def test_init(self, recorder):
        assert recorder.recording == False
        assert recorder.recorded_file is None
        assert len(recorder.audio_chunks) == 0
        assert len(recorder.audio_buffer) == 0
    
    def test_start_recording(self, recorder):
        recorder.start_recording()
        assert recorder.recording == True
        assert recorder.recorded_file is None
        assert len(recorder.audio_chunks) == 0
        assert len(recorder.audio_buffer) == 0
    
    def test_process_audio(self, recorder, mock_audio_frame):
        recorder.start_recording()
        frame = recorder.process_audio(mock_audio_frame)
        assert len(recorder.audio_chunks) > 0
        assert isinstance(frame, MockFrame)
    
    def test_stop_recording(self, recorder, mock_audio_frame):
        recorder.start_recording()
        recorder.process_audio(mock_audio_frame)
        file_path = recorder.stop_recording()
        
        assert file_path is not None
        assert Path(file_path).exists()
        assert recorder.recording == False
        
        # Verify the WAV file
        with wave.open(file_path, 'rb') as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == 16000
        
        # Cleanup
        Path(file_path).unlink()
    
    def test_visualization_buffer(self, recorder, mock_audio_frame):
        recorder.start_recording()
        recorder.process_audio(mock_audio_frame)
        assert len(recorder.audio_buffer) > 0
        
        # Test buffer limits
        for _ in range(2000):  # More than maxlen
            recorder.audio_buffer.append(1.0)
        assert len(recorder.audio_buffer) == 1000  # Should be limited to maxlen 
import streamlit as st
import requests
import json
from pathlib import Path
import tempfile
import os
from streamlit_webrtc import webrtc_streamer, MediaStreamConstraints, RTCConfiguration
import av
import numpy as np
import wave
from datetime import datetime
from typing import Optional
from collections import deque
import time
import logging

# Configure the app
st.set_page_config(
    page_title="CLAWD Agent",
    page_icon="🎙️",
    layout="wide"
)

# Constants
API_BASE_URL = "http://localhost:8000"
SAMPLE_RATE = 16000

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AudioRecorder:
    def __init__(self):
        self.audio_chunks = []
        self.recording = False
        self.recorded_file: Optional[str] = None
        # Add buffer for visualization
        self.audio_buffer = deque(maxlen=1000)  # Store ~1 second of audio at 16kHz
        self.last_update = time.time()

    def start_recording(self):
        self.audio_chunks = []
        self.recording = True
        self.recorded_file = None
        self.audio_buffer.clear()

    def stop_recording(self) -> Optional[str]:
        if not self.audio_chunks:
            return None

        # Create temporary WAV file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        with wave.open(temp_file.name, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b''.join(self.audio_chunks))

        self.recorded_file = temp_file.name
        self.recording = False
        self.audio_buffer.clear()
        return temp_file.name

    def process_audio(self, frame):
        logger.debug(f"Processing audio frame: {frame}")
        if self.recording:
            try:
                sound = frame.to_ndarray(format="s16")
                logger.debug(f"Sound array shape: {sound.shape}")
                sound = sound.reshape(-1)  # Convert to mono
                
                # Add to recording chunks
                self.audio_chunks.append(sound.tobytes())
                
                # Update visualization buffer (downsample if needed)
                current_time = time.time()
                if current_time - self.last_update > 0.05:  # Update every 50ms
                    # Calculate RMS amplitude for visualization
                    chunk_size = 160  # 10ms at 16kHz
                    for i in range(0, len(sound), chunk_size):
                        chunk = sound[i:i + chunk_size]
                        if len(chunk) == chunk_size:  # Only process full chunks
                            rms = np.sqrt(np.mean(chunk.astype(np.float32)**2))
                            self.audio_buffer.append(rms)
                    self.last_update = current_time
                    
            except Exception as e:
                logger.error(f"Error processing audio frame: {e}")
        return frame

def save_uploaded_file(uploaded_file):
    """Save uploaded file to temp directory and return path."""
    try:
        suffix = Path(uploaded_file.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None

def process_audio_file(file_path: str):
    logger.debug(f"Processing file: {file_path}")
    try:
        with open(file_path, 'rb') as f:
            files = {'audio_file': f}
            logger.debug("Sending request to API...")
            response = requests.post(
                f"{API_BASE_URL}/voice/process-voice",
                files=files
            )
            logger.debug(f"API Response: {response.status_code}")
            
        if response.status_code == 200:
            result = response.json()
            
            # Add to logs
            st.session_state.logs.append({
                "type": "transcription",
                "text": result["transcribed_text"],
                "result": result["command_result"]
            })
            
            # Display results
            st.success("Audio processed successfully!")
            st.markdown("#### Transcribed Command:")
            st.write(result["transcribed_text"])
            
            st.markdown("#### Command Result:")
            st.json(result["command_result"])
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Error processing request: {e}")

def main():
    st.title("🎙️ CLAWD Agent")
    st.subheader("Local Computer Use Agent with Whisper Integration")

    # Initialize session state
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'recorder' not in st.session_state:
        st.session_state.recorder = AudioRecorder()

    # Create columns for layout
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 🖥️ Command Input")
        
        # Create tabs for different input methods
        tab1, tab2, tab3 = st.tabs(["Text Command", "Record Audio", "Upload Audio"])
        
        with tab1:
            st.markdown("##### Type your command")
            command = st.text_input("Enter command:", placeholder="e.g., 'open notepad' or 'create a note saying hello world'")
            
            if st.button("🚀 Execute Command"):
                with st.spinner("Processing command..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/voice/process-text",
                            json={"command": command}
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            # Add to logs
                            st.session_state.logs.append({
                                "type": "text_command",
                                "text": command,
                                "result": result
                            })
                            
                            # Display results
                            st.success("Command processed successfully!")
                            
                            if result.get("interpretation"):
                                st.markdown("#### AI Interpretation:")
                                st.write(result["interpretation"])
                            
                            st.markdown("#### Command Result:")
                            st.json(result["command_result"])
                        else:
                            st.error(f"Error: {response.status_code} - {response.text}")
                    except Exception as e:
                        st.error(f"Error processing command: {e}")
        
        with tab2:
            st.markdown("### 🎤 Voice Command Input")
            
            # Create two columns for controls and visualization
            control_col, viz_col = st.columns([1, 3])
            
            with control_col:
                logger.debug("Setting up WebRTC streamer...")
                webrtc_ctx = webrtc_streamer(
                    key="audio-recorder",
                    audio_receiver_size=1024,
                    rtc_configuration=RTCConfiguration(
                        iceServers=[{"urls": ["stun:stun.l.google.com:19302"]}]
                    ),
                    media_stream_constraints=MediaStreamConstraints(
                        audio=True,
                        video=False
                    ),
                    video_processor_factory=None,
                )
                logger.debug(f"WebRTC context: {webrtc_ctx}")
                
                # Recording controls
                if webrtc_ctx.state.playing:
                    if st.button("🔴 Start Recording"):
                        st.session_state.recorder.start_recording()
                        st.info("Recording... Press 'Stop Recording' when done.")
                    
                    if st.button("⏹️ Stop Recording"):
                        if st.session_state.recorder.recording:
                            recorded_file = st.session_state.recorder.stop_recording()
                            if recorded_file:
                                st.success("Recording saved!")
                                st.audio(recorded_file)
                                
                                if st.button("🔍 Process Recording"):
                                    process_audio_file(recorded_file)
                                    # Clean up the temporary file
                                    os.unlink(recorded_file)
            
            with viz_col:
                # Waveform visualization
                if webrtc_ctx.state.playing and st.session_state.recorder.recording:
                    # Create a placeholder for the waveform
                    waveform_placeholder = st.empty()
                    
                    # Update the waveform visualization
                    if len(st.session_state.recorder.audio_buffer) > 0:
                        chart_data = np.array(list(st.session_state.recorder.audio_buffer))
                        # Normalize the data
                        chart_data = chart_data / (np.max(np.abs(chart_data)) + 1e-6)
                        
                        # Display the waveform
                        waveform_placeholder.line_chart(
                            chart_data,
                            height=200,
                            use_container_width=True
                        )
                    else:
                        waveform_placeholder.info("Waiting for audio...")
                
                # Add a volume meter
                if webrtc_ctx.state.playing and st.session_state.recorder.recording:
                    volume_placeholder = st.empty()
                    if len(st.session_state.recorder.audio_buffer) > 0:
                        current_volume = np.mean(list(st.session_state.recorder.audio_buffer)[-10:])
                        normalized_volume = min(1.0, current_volume / 32768.0)  # 16-bit audio
                        volume_placeholder.progress(normalized_volume)
        
        with tab3:
            st.markdown("##### Upload an audio file")
            uploaded_file = st.file_uploader(
                "Choose an audio file",
                type=["wav", "mp3", "m4a"],
                help="Supported formats: WAV, MP3, M4A"
            )

            if uploaded_file:
                st.audio(uploaded_file)
                
                if st.button("🔍 Process Upload"):
                    with st.spinner("Processing audio..."):
                        temp_path = save_uploaded_file(uploaded_file)
                        if temp_path:
                            try:
                                process_audio_file(temp_path)
                            finally:
                                if os.path.exists(temp_path):
                                    os.unlink(temp_path)

    # Command History
    with col2:
        st.markdown("### 📝 Command History")
        
        if st.button("🔄 Clear History"):
            st.session_state.logs = []
        
        for i, log in enumerate(reversed(st.session_state.logs)):
            with st.expander(f"Command {len(st.session_state.logs) - i}", expanded=i == 0):
                st.markdown("**Transcribed Text:**")
                st.write(log["text"])
                st.markdown("**Result:**")
                st.json(log["result"])

if __name__ == "__main__":
    main() 
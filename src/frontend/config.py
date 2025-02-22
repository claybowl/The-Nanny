import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_HOST = os.getenv("CLAWD_API_HOST", "localhost")
API_PORT = os.getenv("CLAWD_API_PORT", "8000")
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"

# File Upload Configuration
ALLOWED_AUDIO_FORMATS = ["wav", "mp3", "m4a"]
MAX_UPLOAD_SIZE_MB = 10

# Paths
TEMP_DIR = Path("/tmp/clawd_uploads")
TEMP_DIR.mkdir(parents=True, exist_ok=True) 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes.voice import router as voice_router
from datetime import datetime

app = FastAPI(
    title="CLAWD Agent API",
    description="Local Computer Use Agent with Whisper Integration",
    version="0.1.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your client URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the voice router
app.include_router(voice_router, prefix="/voice", tags=["voice"])

@app.get("/")
async def root():
    return {"message": "Welcome to CLAWD Agent API"}

@app.get("/test")
async def test_endpoint():
    return {"status": "API is working", "timestamp": datetime.now().isoformat()} 
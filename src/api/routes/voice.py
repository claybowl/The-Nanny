from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
import tempfile
import os
from dotenv import load_dotenv
import logging
from pydantic import BaseModel

from src.voice.whisper_handler import WhisperSTT
from src.core.agent import ComputerAgent
from src.core.ai_services import AIServices, AIServiceError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

router = APIRouter()

try:
    whisper_handler = WhisperSTT(use_api=True)  # Use OpenAI's Whisper API
    computer_agent = ComputerAgent()
    ai_services = AIServices()
    logger.info("Voice route services initialized successfully")
except AIServiceError as e:
    logger.error(f"Failed to initialize AI services: {str(e)}")
    raise
except Exception as e:
    logger.error(f"Unexpected error during initialization: {str(e)}")
    raise

class TextCommand(BaseModel):
    command: str

@router.post("/process-text")
async def process_text_command(command_data: TextCommand):
    """Process a text-based command."""
    try:
        logger.info(f"Processing text command: {command_data.command}")
        
        # Get AI interpretation of the command
        try:
            logger.info("Getting AI interpretation of command")
            interpretation = await ai_services.get_claude_response(
                f"Interpret this command and explain what the user wants to do: {command_data.command}"
            )
            
            if not interpretation:
                logger.warning("Failed to get AI interpretation, proceeding without it")
        except AIServiceError as e:
            logger.error(f"AI service error during interpretation: {str(e)}")
            interpretation = None
        
        # Execute the command
        try:
            logger.info("Executing command")
            result = await computer_agent.execute_command(command_data.command)
            
            return {
                "status": "success",
                "command": command_data.command,
                "interpretation": interpretation,
                "command_result": result
            }
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            raise HTTPException(500, f"Command execution failed: {str(e)}")
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(500, f"Unexpected error: {str(e)}")

@router.post("/process-voice")
async def process_voice_command(audio_file: UploadFile = File(...)):
    """Process voice command from audio file."""
    if not audio_file.filename.endswith(('.mp3', '.wav', '.m4a')):
        logger.warning(f"Unsupported file format: {audio_file.filename}")
        raise HTTPException(400, "Unsupported file format")
    
    logger.info(f"Processing voice command from file: {audio_file.filename}")
    
    # Create temporary file to store uploaded audio
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        try:
            # Write uploaded file to temp file
            content = await audio_file.read()
            temp_file.write(content)
            temp_file.flush()
            
            # Transcribe audio
            logger.info("Starting audio transcription")
            transcribed_text = await whisper_handler.transcribe(temp_file.name)
            
            if not transcribed_text:
                logger.error("Transcription failed")
                raise HTTPException(500, "Transcription failed")
            
            logger.info(f"Transcription successful: {transcribed_text}")
            
            # Get AI interpretation of the command
            try:
                logger.info("Getting AI interpretation of command")
                interpretation = await ai_services.get_claude_response(
                    f"Interpret this voice command and explain what the user wants to do: {transcribed_text}"
                )
                
                if not interpretation:
                    logger.warning("Failed to get AI interpretation, proceeding without it")
            except AIServiceError as e:
                logger.error(f"AI service error during interpretation: {str(e)}")
                interpretation = None
            
            # Execute the command
            try:
                logger.info("Executing command")
                result = await computer_agent.execute_command(transcribed_text)
                
                return {
                    "status": "success",
                    "transcribed_text": transcribed_text,
                    "interpretation": interpretation,
                    "command_result": result
                }
            except Exception as e:
                logger.error(f"Command execution failed: {str(e)}")
                raise HTTPException(500, f"Command execution failed: {str(e)}")
            
        except AIServiceError as e:
            logger.error(f"AI service error: {str(e)}")
            raise HTTPException(503, f"AI service error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(500, f"Unexpected error: {str(e)}")
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                logger.error(f"Failed to clean up temp file: {str(e)}")

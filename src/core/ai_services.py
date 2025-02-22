import os
from typing import Optional
import openai
import anthropic
from anthropic import AsyncAnthropic
from dotenv import load_dotenv
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    pass

class AIServices:
    """Handler for AI service integrations (OpenAI and Anthropic)"""
    
    def __init__(self):
        # Validate API keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not self.openai_api_key or self.openai_api_key == "your-openai-api-key":
            logger.error("OpenAI API key not properly configured")
            raise AIServiceError("OpenAI API key not properly configured")
            
        if not self.anthropic_api_key or self.anthropic_api_key == "your-anthropic-api-key":
            logger.error("Anthropic API key not properly configured")
            raise AIServiceError("Anthropic API key not properly configured")
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(
            api_key=self.openai_api_key
        )
        
        # Initialize Anthropic client (async version)
        self.claude_client = AsyncAnthropic(
            api_key=self.anthropic_api_key
        )
        
        logger.info("AI Services initialized successfully")
    
    async def get_gpt_response(self, prompt: str, model: str = "gpt-3.5-turbo", max_retries: int = 2) -> Optional[str]:
        """Get response from OpenAI's GPT models.
        
        Args:
            prompt: The input prompt
            model: The GPT model to use
            max_retries: Maximum number of retry attempts
            
        Returns:
            Generated response or None if request fails
        """
        attempt = 0
        while attempt <= max_retries:
            try:
                logger.info(f"Sending request to GPT (attempt {attempt + 1})")
                response = await self.openai_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content
            except openai.RateLimitError:
                if attempt == max_retries:
                    logger.error("Rate limit exceeded and max retries reached")
                    raise AIServiceError("OpenAI rate limit exceeded")
                logger.warning("Rate limit hit, retrying...")
                attempt += 1
            except Exception as e:
                logger.error(f"GPT request error: {str(e)}")
                return None
    
    async def get_claude_response(self, prompt: str, model: str = "claude-3-sonnet-20240229", max_retries: int = 2) -> Optional[str]:
        """Get response from Anthropic's Claude.
        
        Args:
            prompt: The input prompt
            model: The Claude model to use
            max_retries: Maximum number of retry attempts
            
        Returns:
            Generated response or None if request fails
        """
        attempt = 0
        while attempt <= max_retries:
            try:
                logger.info(f"Sending request to Claude (attempt {attempt + 1})")
                message = await self.claude_client.messages.create(
                    model=model,
                    max_tokens=1000,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return message.content[0].text
            except anthropic.RateLimitError:
                if attempt == max_retries:
                    logger.error("Rate limit exceeded and max retries reached")
                    raise AIServiceError("Anthropic rate limit exceeded")
                logger.warning("Rate limit hit, retrying...")
                attempt += 1
            except Exception as e:
                logger.error(f"Claude request error: {str(e)}")
                return None
    
    async def transcribe_audio_with_whisper_api(self, audio_file_path: str, max_retries: int = 2) -> Optional[str]:
        """Transcribe audio using OpenAI's Whisper API.
        
        Args:
            audio_file_path: Path to the audio file
            max_retries: Maximum number of retry attempts
            
        Returns:
            Transcribed text or None if transcription fails
        """
        attempt = 0
        while attempt <= max_retries:
            try:
                logger.info(f"Sending request to Whisper API (attempt {attempt + 1})")
                with open(audio_file_path, "rb") as audio_file:
                    response = await self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                return response.text
            except openai.RateLimitError:
                if attempt == max_retries:
                    logger.error("Rate limit exceeded and max retries reached")
                    raise AIServiceError("OpenAI rate limit exceeded")
                logger.warning("Rate limit hit, retrying...")
                attempt += 1
            except Exception as e:
                logger.error(f"Whisper API error: {str(e)}")
                return None

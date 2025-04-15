"""
Module for transcribing audio files using Gemini API.
"""
import logging
import os
from typing import Optional, Union, Dict, Any

from google import genai
from google.genai.types import HttpOptions, Part, GenerateContentConfig

from transcriber.models import Transcript

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_audio(
    gcs_uri: str, 
    job_id: str, 
    start_timestamp: float = 0.0, 
    end_timestamp: Optional[float] = None
) -> Transcript:
    """
    Process an audio file and generate a transcript using Gemini API.
    
    Args:
        gcs_uri: GCS URI of the audio file
        job_id: Unique job ID
        start_timestamp: Start timestamp in seconds
        end_timestamp: End timestamp in seconds
        
    Returns:
        Transcript: Generated transcript
    """
    try:
        logger.info(f"Processing audio file: {gcs_uri}")
        
        # Set up the client with timestamp configuration
        client = genai.Client(http_options=HttpOptions(api_version="v1"))
        
        # Prepare the transcription prompt with timestamp information
        timestamp_info = f"Start: {format_timestamp(start_timestamp)}"
        if end_timestamp:
            timestamp_info += f", End: {format_timestamp(end_timestamp)}"
        
        prompt = f"""
        <task>
        Transcribe the audio in SRT format for short format content.
        This is chunk of a larger YouTube video from {timestamp_info}.
        </task>
        <input>Audio will be provided to you</input>

        <guidelines> 
        - Transcribe in the original language of the video
        - If the video is in Hindi or mixed Hindi-English (Hinglish), use Roman script for Hindi words
        - Capture natural language mix
        - Differentiate speakers clearly (Speaker 1, Speaker 2, etc.)
        - Include all dialogue nuances
        - Ensure timestamps are in SRT format (HH:MM:SS,MMM)
        - Keep subtitle length between 3-5 words per segment
        - Maintain continuity with the timing information provided
        </guidelines>

        <output>
        <entire_transcript>
        1
        00:00:00,000 --> 00:00:05,000  
        Speaker X: Transcription text

        2
        00:00:05,000 --> 00:00:10,000  
        Speaker X: Transcription text

        ...
        </entire_transcript>
        
        Return the transcript as a JSON object with the following structure:
        {{
            "text": "The full SRT formatted transcript",
            "duration": "The total duration of this audio chunk in seconds"
        }}
        </output>
        """
        
        try:
            # Generate transcription
            response = client.models.generate_content(
                model="gemini-2.0-flash-001",
                contents=[
                    prompt,
                    Part.from_uri(
                        file_uri=gcs_uri,
                        mime_type="audio/mpeg",
                    ),
                ],
                config=GenerateContentConfig(
                    audio_timestamp=True, 
                    response_mime_type='application/json', 
                    response_schema=Transcript
                ),
            )
            logger.info("Transcription completed successfully")

        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise e
        
        # Extract transcript from response
        transcript: Transcript = response.parsed
        
        return transcript
    
    except Exception as e:
        logger.error(f"Error in processing audio: {str(e)}")
        raise str(e)

def format_timestamp(seconds: float) -> str:
    """
    Format a timestamp in seconds to HH:MM:SS format.
    
    Args:
        seconds: Timestamp in seconds
        
    Returns:
        str: Formatted timestamp
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
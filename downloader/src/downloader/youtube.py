"""
YouTube downloader module using Pytubefix.
This module handles downloading audio from YouTube videos.
"""
import os
import logging
import tempfile
from typing import Optional, List, Dict, Any
import pytubefix
from pydantic import HttpUrl

logger = logging.getLogger(__name__)

async def download_audio(
    url: HttpUrl, 
    output_dir: Optional[str] = None,
    audio_format: str = "mp4"
) -> str:
    """
    Download audio from a YouTube video.
    
    Args:
        url: YouTube video URL
        output_dir: Directory to save the audio file (default: temporary directory)
        audio_format: Audio format (default: "mp4")
        
    Returns:
        str: Path to the downloaded audio file
    """
    try:
        # Create temporary directory if not specified
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract video ID and create a filename
        video_id = str(url).split("v=")[-1].split("&")[0]
        output_file = os.path.join(output_dir, f"{video_id}.{audio_format}")
        
        # Download audio using pytubefix
        yt = pytubefix.YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        
        if not audio_stream:
            raise ValueError(f"No audio stream found for {url}")
        
        # Download the audio
        logger.info(f"Downloading audio from {url}")
        audio_path = audio_stream.download(output_path=output_dir, filename=f"{video_id}.{audio_format}")
        logger.info(f"Downloaded audio to {audio_path}")
        
        return audio_path
        
    except Exception as e:
        logger.error(f"Error downloading audio from {url}: {str(e)}")
        raise

async def get_video_metadata(url: HttpUrl) -> Dict[str, Any]:
    """
    Get metadata for a YouTube video.
    
    Args:
        url: YouTube video URL
        
    Returns:
        Dict: Video metadata
    """
    try:
        yt = pytubefix.YouTube(url)
        
        return {
            "title": yt.title,
            "author": yt.author,
            "length_seconds": yt.length,
            "publish_date": str(yt.publish_date) if yt.publish_date else None,
            "video_id": yt.video_id,
            "views": yt.views,
            "description": yt.description
        }
    except Exception as e:
        logger.error(f"Error getting metadata for {url}: {str(e)}")
        raise
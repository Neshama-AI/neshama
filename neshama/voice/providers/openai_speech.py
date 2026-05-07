# OpenAI Speech Provider
"""
OpenAI TTS/STT Adapter

API Endpoints:
- TTS: POST https://api.openai.com/v1/audio/speech
- STT: POST https://api.openai.com/v1/audio/transcriptions

Pricing:
- tts-1: $15/million characters
- tts-1-hd: $30/million characters
- Whisper: $0.006/minute
"""

import os
from typing import Dict, List, Optional, AsyncIterator
import logging

from ..base import (
    VoiceProvider,
    VoiceInfo,
    ProviderInfo,
    TTSOptions,
    STTOptions,
    TTSResult,
    STTResult,
    EmotionStyle,
    VoiceError,
    AuthenticationError,
    RateLimitError,
    TextTooLongError,
)

logger = logging.getLogger(__name__)

# OpenAI API endpoint
DEFAULT_API_URL = "https://api.openai.com/v1"

# OpenAI TTS voices
OPENAI_VOICES = [
    VoiceInfo(voice_id="alloy", name="Alloy", language="en", gender="neutral", style="neutral", provider="openai"),
    VoiceInfo(voice_id="echo", name="Echo", language="en", gender="male", style="warm", provider="openai"),
    VoiceInfo(voice_id="fable", name="Fable", language="en", gender="male", style="british", provider="openai"),
    VoiceInfo(voice_id="onyx", name="Onyx", language="en", gender="male", style="deep", provider="openai"),
    VoiceInfo(voice_id="nova", name="Nova", language="en", gender="female", style="cheerful", provider="openai"),
    VoiceInfo(voice_id="shimmer", name="Shimmer", language="en", gender="female", style="soft", provider="openai"),
]

# Emotion to speed adjustment for OpenAI (OpenAI doesn't natively support emotion)
EMOTION_SPEED_MAP: Dict[EmotionStyle, float] = {
    EmotionStyle.JOY: 1.1,
    EmotionStyle.ANGER: 1.0,
    EmotionStyle.SADNESS: 0.85,
    EmotionStyle.FEAR: 1.15,
    EmotionStyle.TRUST: 0.95,
    EmotionStyle.SURPRISE: 1.1,
    EmotionStyle.DISGUST: 0.95,
    EmotionStyle.ANTICIPATION: 1.05,
    EmotionStyle.NEUTRAL: 1.0,
}


class OpenAISpeechProvider(VoiceProvider):
    """
    OpenAI TTS/STT provider.
    
    Supports:
    - TTS with tts-1 and tts-1-hd models
    - STT with Whisper model
    - Streaming synthesis
    - Multiple voice options
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize OpenAI Speech provider.
        
        Config options:
        - api_key: OpenAI API key
        - model: TTS model (tts-1 or tts-1-hd)
        - api_url: Base API URL (optional)
        """
        super().__init__(config)
        self.api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")
        self.model = self.config.get("model", "tts-1")
        self.api_url = self.config.get("api_url") or DEFAULT_API_URL
        
        if not self.api_key:
            logger.warning("OpenAI API key not configured")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def get_provider_info(self) -> ProviderInfo:
        """Get provider information."""
        return ProviderInfo(
            name="openai",
            supported_languages=["en"],  # OpenAI TTS primarily supports English
            max_text_length=4096,
            supports_emotion=False,  # OpenAI TTS doesn't support emotion parameters
            supports_streaming=True,
            pricing={
                "tts_per_char": 0.000015 if self.model == "tts-1" else 0.000030,
                "stt_per_second": 0.0001,
            },
            provider_type="cloud",
        )
    
    def list_voices(self, language: Optional[str] = None) -> List[VoiceInfo]:
        """
        List available voices.
        """
        if not language:
            return OPENAI_VOICES
        
        return [v for v in OPENAI_VOICES if v.language.startswith(language.split("-")[0])]
    
    async def text_to_speech(
        self,
        text: str,
        options: TTSOptions,
    ) -> TTSResult:
        """
        Convert text to speech using OpenAI API.
        
        Args:
            text: Text to synthesize
            options: TTS options
            
        Returns:
            TTSResult with audio data
        """
        if not self.api_key:
            raise AuthenticationError("OpenAI API key not configured", provider="openai")
        
        if len(text) > self.get_provider_info().max_text_length:
            raise TextTooLongError(
                f"Text length {len(text)} exceeds maximum",
                provider="openai"
            )
        
        # Build request
        request_data = {
            "model": self.model,
            "input": text,
            "voice": options.voice_id,
            "response_format": "mp3",
            "speed": EMOTION_SPEED_MAP.get(options.emotion, 1.0) if options.emotion else 1.0,
        }
        
        import aiohttp
        
        url = f"{self.api_url}/audio/speech"
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                
                async with session.post(
                    url,
                    json=request_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 401:
                        raise AuthenticationError("Invalid OpenAI API key", provider="openai")
                    elif response.status == 429:
                        raise RateLimitError("OpenAI rate limit exceeded", provider="openai")
                    elif response.status != 200:
                        text_err = await response.text()
                        raise VoiceError(
                            f"OpenAI API error: {response.status} - {text_err}",
                            provider="openai"
                        )
                    
                    audio_data = await response.read()
                    
                    return TTSResult(
                        audio_data=audio_data,
                        duration_seconds=len(audio_data) / 24000,
                        format="mp3",
                        voice_id=options.voice_id,
                        provider="openai",
                    )
        except aiohttp.ClientError as e:
            raise VoiceError(f"Network error: {str(e)}", provider="openai")
    
    async def text_to_speech_stream(
        self,
        text: str,
        options: TTSOptions,
    ) -> AsyncIterator[bytes]:
        """
        Convert text to speech with streaming audio chunks.
        """
        if not self.api_key:
            raise AuthenticationError("OpenAI API key not configured", provider="openai")
        
        request_data = {
            "model": self.model,
            "input": text,
            "voice": options.voice_id,
            "response_format": "mp3",
            "speed": EMOTION_SPEED_MAP.get(options.emotion, 1.0) if options.emotion else 1.0,
        }
        
        import aiohttp
        
        url = f"{self.api_url}/audio/speech"
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                
                async with session.post(
                    url,
                    json=request_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status != 200:
                        text_err = await response.text()
                        raise VoiceError(
                            f"OpenAI streaming error: {response.status}",
                            provider="openai"
                        )
                    
                    async for chunk in response.content.iter_chunked(8192):
                        if chunk:
                            yield chunk
        except aiohttp.ClientError as e:
            raise VoiceError(f"Network error: {str(e)}", provider="openai")
    
    async def speech_to_text(
        self,
        audio_data: bytes,
        options: STTOptions,
    ) -> STTResult:
        """
        Convert speech to text using OpenAI Whisper API.
        
        Args:
            audio_data: Audio data to transcribe
            options: STT options
            
        Returns:
            STTResult with transcribed text
        """
        if not self.api_key:
            raise AuthenticationError("OpenAI API key not configured", provider="openai")
        
        import aiohttp
        
        url = f"{self.api_url}/audio/transcriptions"
        
        try:
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                form.add_field(
                    "file",
                    audio_data,
                    filename="audio.mp3",
                    content_type="audio/mpeg",
                )
                form.add_field("model", "whisper-1")
                if options.language:
                    form.add_field("language", options.language)
                
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                async with session.post(
                    url,
                    data=form,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status != 200:
                        text_err = await response.text()
                        raise VoiceError(
                            f"OpenAI STT error: {response.status} - {text_err}",
                            provider="openai"
                        )
                    
                    result = await response.json()
                    
                    return STTResult(
                        text=result.get("text", ""),
                        confidence=0.95,  # Whisper doesn't return confidence
                        language=options.language or "en",
                        provider="openai",
                    )
        except aiohttp.ClientError as e:
            raise VoiceError(f"Network error: {str(e)}", provider="openai")

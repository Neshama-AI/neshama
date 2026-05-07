# ElevenLabs Provider
"""
ElevenLabs TTS/STT Adapter

API Endpoints:
- TTS: POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}
- STT: POST https://api.elevenlabs.io/v1/speech-to-text
- Voices: GET https://api.elevenlabs.io/v1/voices

Pricing:
- Standard: $0.18/1K characters
- Pro Voice Cloning: $0.30/1K characters
"""

import os
from typing import Dict, List, Optional, AsyncIterator
import asyncio
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

# Default API endpoint
DEFAULT_API_URL = "https://api.elevenlabs.io/v1"

# Emotion style mapping for ElevenLabs
ELEVENLABS_EMOTION_MAP: Dict[EmotionStyle, Dict[str, float]] = {
    EmotionStyle.JOY: {
        "stability": 0.3,
        "similarity_boost": 0.8,
        "style": 0.8,
    },
    EmotionStyle.ANGER: {
        "stability": 0.5,
        "similarity_boost": 0.7,
        "style": 1.0,
    },
    EmotionStyle.SADNESS: {
        "stability": 0.7,
        "similarity_boost": 0.6,
        "style": 0.2,
    },
    EmotionStyle.FEAR: {
        "stability": 0.2,
        "similarity_boost": 0.8,
        "style": 0.9,
    },
    EmotionStyle.TRUST: {
        "stability": 0.8,
        "similarity_boost": 0.7,
        "style": 0.3,
    },
    EmotionStyle.SURPRISE: {
        "stability": 0.3,
        "similarity_boost": 0.9,
        "style": 1.0,
    },
    EmotionStyle.DISGUST: {
        "stability": 0.4,
        "similarity_boost": 0.6,
        "style": 0.7,
    },
    EmotionStyle.ANTICIPATION: {
        "stability": 0.4,
        "similarity_boost": 0.8,
        "style": 0.6,
    },
    EmotionStyle.NEUTRAL: {
        "stability": 0.5,
        "similarity_boost": 0.75,
        "style": 0.0,
    },
}


class ElevenLabsProvider(VoiceProvider):
    """
    ElevenLabs TTS/STT provider.
    
    Supports:
    - Text-to-speech with emotion control
    - Speech-to-text
    - Voice cloning
    - Streaming synthesis
    - 40+ languages
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize ElevenLabs provider.
        
        Config options:
        - api_key: ElevenLabs API key (xi-api-key)
        - api_url: Base API URL (optional)
        - model_id: TTS model ID (optional, default: eleven_multilingual_v2)
        """
        super().__init__(config)
        self.api_key = self.config.get("api_key") or os.getenv("ELEVENLABS_API_KEY")
        self.api_url = self.config.get("api_url") or DEFAULT_API_URL
        self.model_id = self.config.get("model_id", "eleven_multilingual_v2")
        
        if not self.api_key:
            logger.warning("ElevenLabs API key not configured")
    
    def _setup(self):
        """Setup HTTP client."""
        # Will be mocked in tests
        self._client = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with authentication."""
        return {
            "xi-api-key": self.api_key or "",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    def get_provider_info(self) -> ProviderInfo:
        """Get provider information."""
        return ProviderInfo(
            name="elevenlabs",
            supported_languages=[
                "en", "en-US", "en-GB", "en-AU", "en-CA", "en-IN",
                "zh", "zh-CN", "zh-TW", "zh-HK",
                "es", "es-ES", "es-MX", "es-US",
                "fr", "fr-FR", "fr-CA",
                "de", "de-DE",
                "it", "it-IT",
                "pt", "pt-BR", "pt-PT",
                "ja", "ko", "ar", "ru", "nl", "pl", "sv", "tr", "hi",
            ],
            max_text_length=5000,
            supports_emotion=True,
            supports_streaming=True,
            pricing={
                "tts_per_char": 0.00018,
                "stt_per_second": 0.01,
            },
            provider_type="cloud",
        )
    
    def list_voices(self, language: Optional[str] = None) -> List[VoiceInfo]:
        """
        List available voices.
        
        In production, this would fetch from the API.
        Returns default voices for testing.
        """
        # Default voices (would be fetched from API in production)
        default_voices = [
            VoiceInfo(
                voice_id="21m00Tcm4TlvDq8ikWAM",
                name="Rachel",
                language="en-US",
                gender="female",
                style="casual",
                provider="elevenlabs",
            ),
            VoiceInfo(
                voice_id="pFZP5JQG7iQjIQuC4Bku",
                name="Domi",
                language="en-US",
                gender="female",
                style="bold",
                provider="elevenlabs",
            ),
            VoiceInfo(
                voice_id="TX3LPaxmHKxFdv7VOQHJ",
                name="Fin",
                language="en-US",
                gender="male",
                style="dramatic",
                provider="elevenlabs",
            ),
            VoiceInfo(
                voice_id="VR6AewLTigWG4xSOukaG",
                name="Charlie",
                language="en-US",
                gender="male",
                style="chill",
                provider="elevenlabs",
            ),
            VoiceInfo(
                voice_id="bIHbis24MMJ80QmchFwu",
                name="Annie",
                language="en-US",
                gender="female",
                style="calm",
                provider="elevenlabs",
            ),
            VoiceInfo(
                voice_id="EXAVITQu4vr4xnSDxMaL",
                name="Bella",
                language="en-US",
                gender="female",
                style="emotional",
                provider="elevenlabs",
            ),
            VoiceInfo(
                voice_id="AZnzlk1XvdvUeBnXmlld",
                name="Droid",
                language="en-US",
                gender="neutral",
                style="robotic",
                provider="elevenlabs",
            ),
            VoiceInfo(
                voice_id="ErXwobaYiN019PkyB4Gj",
                name="Aria",
                language="en-US",
                gender="female",
                style="natural",
                provider="elevenlabs",
            ),
        ]
        
        if not language:
            return default_voices
        
        return [v for v in default_voices if v.language.startswith(language.split("-")[0])]
    
    async def text_to_speech(
        self,
        text: str,
        options: TTSOptions,
    ) -> TTSResult:
        """
        Convert text to speech using ElevenLabs API.
        
        Args:
            text: Text to synthesize
            options: TTS options
            
        Returns:
            TTSResult with audio data
        """
        if not self.api_key:
            raise AuthenticationError("ElevenLabs API key not configured", provider="elevenlabs")
        
        if len(text) > self.get_provider_info().max_text_length:
            raise TextTooLongError(
                f"Text length {len(text)} exceeds maximum {self.get_provider_info().max_text_length}",
                provider="elevenlabs"
            )
        
        # Build request
        emotion_params = self._get_emotion_params(options.emotion)
        
        request_data = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": emotion_params.get("stability", 0.5),
                "similarity_boost": emotion_params.get("similarity_boost", 0.75),
                "style": emotion_params.get("style", 0.0),
                "use_speaker_boost": True,
            },
        }
        
        if options.language:
            request_data["language"] = options.language
        
        # Make API request (will be mocked in tests)
        import aiohttp
        
        url = f"{self.api_url}/text-to-speech/{options.voice_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                }
                
                async with session.post(
                    url,
                    json=request_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 401:
                        raise AuthenticationError("Invalid ElevenLabs API key", provider="elevenlabs")
                    elif response.status == 429:
                        raise RateLimitError("ElevenLabs rate limit exceeded", provider="elevenlabs")
                    elif response.status != 200:
                        text = await response.text()
                        raise VoiceError(
                            f"ElevenLabs API error: {response.status} - {text}",
                            provider="elevenlabs"
                        )
                    
                    audio_data = await response.read()
                    
                    return TTSResult(
                        audio_data=audio_data,
                        duration_seconds=len(audio_data) / 24000,  # Estimate
                        format="mp3",
                        voice_id=options.voice_id,
                        provider="elevenlabs",
                    )
        except aiohttp.ClientError as e:
            raise VoiceError(f"Network error: {str(e)}", provider="elevenlabs")
    
    async def text_to_speech_stream(
        self,
        text: str,
        options: TTSOptions,
    ) -> AsyncIterator[bytes]:
        """
        Convert text to speech with streaming audio chunks.
        
        Args:
            text: Text to synthesize
            options: TTS options
            
        Yields:
            Audio chunks
        """
        if not self.api_key:
            raise AuthenticationError("ElevenLabs API key not configured", provider="elevenlabs")
        
        emotion_params = self._get_emotion_params(options.emotion)
        
        request_data = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": emotion_params.get("stability", 0.5),
                "similarity_boost": emotion_params.get("similarity_boost", 0.75),
                "style": emotion_params.get("style", 0.0),
                "use_speaker_boost": True,
            },
        }
        
        if options.language:
            request_data["language"] = options.language
        
        import aiohttp
        
        url = f"{self.api_url}/text-to-speech/{options.voice_id}/stream"
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                }
                
                async with session.post(
                    url,
                    json=request_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status != 200:
                        text = await response.text()
                        raise VoiceError(
                            f"ElevenLabs streaming error: {response.status} - {text}",
                            provider="elevenlabs"
                        )
                    
                    async for chunk in response.content.iter_chunked(8192):
                        if chunk:
                            yield chunk
        except aiohttp.ClientError as e:
            raise VoiceError(f"Network error: {str(e)}", provider="elevenlabs")
    
    async def speech_to_text(
        self,
        audio_data: bytes,
        options: STTOptions,
    ) -> STTResult:
        """
        Convert speech to text using ElevenLabs API.
        
        Args:
            audio_data: Audio data to transcribe
            options: STT options
            
        Returns:
            STTResult with transcribed text
        """
        if not self.api_key:
            raise AuthenticationError("ElevenLabs API key not configured", provider="elevenlabs")
        
        import aiohttp
        
        url = f"{self.api_url}/speech-to-text"
        
        try:
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                form.add_field(
                    "audio",
                    audio_data,
                    filename="audio.mp3",
                    content_type="audio/mpeg",
                )
                form.add_field("language", options.language or "en")
                
                headers = {"xi-api-key": self.api_key}
                
                async with session.post(
                    url,
                    data=form,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status != 200:
                        text = await response.text()
                        raise VoiceError(
                            f"ElevenLabs STT error: {response.status} - {text}",
                            provider="elevenlabs"
                        )
                    
                    result = await response.json()
                    
                    return STTResult(
                        text=result.get("text", ""),
                        confidence=result.get("confidence", 1.0),
                        language=options.language,
                        provider="elevenlabs",
                    )
        except aiohttp.ClientError as e:
            raise VoiceError(f"Network error: {str(e)}", provider="elevenlabs")
    
    def _get_emotion_params(self, emotion: Optional[EmotionStyle]) -> Dict[str, float]:
        """Get ElevenLabs voice settings for emotion."""
        if not emotion:
            return ELEVENLABS_EMOTION_MAP[EmotionStyle.NEUTRAL]
        return ELEVENLABS_EMOTION_MAP.get(emotion, ELEVENLABS_EMOTION_MAP[EmotionStyle.NEUTRAL])

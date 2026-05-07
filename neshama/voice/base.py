# Voice Provider Base Classes
"""
VoiceProvider - Abstract base class for TTS/STT providers.

All voice providers must inherit from this class and implement:
- text_to_speech: Convert text to audio
- speech_to_text: Convert audio to text
- list_voices: List available voices
- get_provider_info: Get provider metadata
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, AsyncIterator, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EmotionStyle(Enum):
    """Emotion styles for TTS."""
    JOY = "joy"
    ANGER = "anger"
    SADNESS = "sadness"
    FEAR = "fear"
    TRUST = "trust"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    ANTICIPATION = "anticipation"
    NEUTRAL = "neutral"


# Emotion to voice style mapping
EMOTION_STYLE_MAPPING: Dict[EmotionStyle, Dict[str, any]] = {
    EmotionStyle.JOY: {
        "style": "cheerful",
        "pitch": "high",
        "speed": 1.1,
        "description": "cheerful, higher pitch"
    },
    EmotionStyle.ANGER: {
        "style": "intense",
        "pitch": "low",
        "speed": 1.0,
        "description": "intense, lower pitch"
    },
    EmotionStyle.SADNESS: {
        "style": "somber",
        "pitch": "low",
        "speed": 0.85,
        "description": "slow, softer"
    },
    EmotionStyle.FEAR: {
        "style": "shaky",
        "pitch": "high",
        "speed": 1.2,
        "description": "shaky, faster"
    },
    EmotionStyle.TRUST: {
        "style": "warm",
        "pitch": "medium",
        "speed": 0.95,
        "description": "warm, calm"
    },
    EmotionStyle.SURPRISE: {
        "style": "excited",
        "pitch": "high",
        "speed": 1.15,
        "description": "excited, varied pitch"
    },
    EmotionStyle.DISGUST: {
        "style": "contemptuous",
        "pitch": "low",
        "speed": 0.9,
        "description": "contemptuous, sneering"
    },
    EmotionStyle.ANTICIPATION: {
        "style": "eager",
        "pitch": "medium-high",
        "speed": 1.1,
        "description": "eager, expectant"
    },
    EmotionStyle.NEUTRAL: {
        "style": "neutral",
        "pitch": "medium",
        "speed": 1.0,
        "description": "neutral, balanced"
    },
}


@dataclass
class VoiceInfo:
    """Voice metadata."""
    voice_id: str
    name: str
    language: str
    gender: str  # male/female/neutral
    style: str   # casual/formal/dramatic/whisper
    preview_url: str = ""
    
    # Optional properties
    age_range: str = ""  # e.g., "young", "middle-aged", "senior"
    accent: str = ""     # e.g., "american", "british", "australian"
    provider: str = ""   # Which provider this voice belongs to
    
    def to_dict(self) -> Dict:
        return {
            "voice_id": self.voice_id,
            "name": self.name,
            "language": self.language,
            "gender": self.gender,
            "style": self.style,
            "preview_url": self.preview_url,
            "age_range": self.age_range,
            "accent": self.accent,
            "provider": self.provider,
        }


@dataclass
class ProviderInfo:
    """Provider metadata and capabilities."""
    name: str
    supported_languages: List[str]
    max_text_length: int
    supports_emotion: bool
    supports_streaming: bool
    pricing: Dict[str, float]  # e.g., {"tts_per_char": 0.00018, "stt_per_second": 0.001}
    provider_type: str = "cloud"  # cloud/local
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "supported_languages": self.supported_languages,
            "max_text_length": self.max_text_length,
            "supports_emotion": self.supports_emotion,
            "supports_streaming": self.supports_streaming,
            "pricing": self.pricing,
            "provider_type": self.provider_type,
        }


@dataclass
class TTSOptions:
    """Options for TTS synthesis."""
    voice_id: str
    language: str = "en"
    emotion: Optional[EmotionStyle] = None
    speed: float = 1.0
    pitch: float = 1.0
    format: str = "mp3"  # mp3, wav, ogg
    sample_rate: int = 24000
    
    def to_dict(self) -> Dict:
        return {
            "voice_id": self.voice_id,
            "language": self.language,
            "emotion": self.emotion.value if self.emotion else None,
            "speed": self.speed,
            "pitch": self.pitch,
            "format": self.format,
            "sample_rate": self.sample_rate,
        }


@dataclass
class STTOptions:
    """Options for STT transcription."""
    language: str = "en"
    max_duration_seconds: int = 60
    format: str = "mp3"  # mp3, wav, ogg, webm
    
    def to_dict(self) -> Dict:
        return {
            "language": self.language,
            "max_duration_seconds": self.max_duration_seconds,
            "format": self.format,
        }


@dataclass
class TTSResult:
    """Result of TTS synthesis."""
    audio_data: bytes
    duration_seconds: float
    format: str
    voice_id: str
    provider: str
    cached: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "duration_seconds": self.duration_seconds,
            "format": self.format,
            "voice_id": self.voice_id,
            "provider": self.provider,
            "cached": self.cached,
        }


@dataclass
class STTResult:
    """Result of STT transcription."""
    text: str
    confidence: float
    language: str
    provider: str
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "language": self.language,
            "provider": self.provider,
            "duration_seconds": self.duration_seconds,
        }


class VoiceProvider(ABC):
    """
    Abstract base class for voice providers.
    
    All TTS/STT providers must implement these methods.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the provider.
        
        Args:
            config: Provider-specific configuration (API keys, endpoints, etc.)
        """
        self.config = config or {}
        self._setup()
    
    def _setup(self):
        """Setup provider-specific resources. Override in subclasses."""
        pass
    
    @abstractmethod
    async def text_to_speech(
        self,
        text: str,
        options: TTSOptions,
    ) -> TTSResult:
        """
        Convert text to speech.
        
        Args:
            text: Text to synthesize
            options: TTS options including voice, language, emotion
            
        Returns:
            TTSResult with audio data
            
        Raises:
            VoiceError: If synthesis fails
        """
        pass
    
    @abstractmethod
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
            Audio chunks as they are generated
            
        Raises:
            VoiceError: If synthesis fails
        """
        pass
    
    @abstractmethod
    async def speech_to_text(
        self,
        audio_data: bytes,
        options: STTOptions,
    ) -> STTResult:
        """
        Convert speech audio to text.
        
        Args:
            audio_data: Audio data to transcribe
            options: STT options including language
            
        Returns:
            STTResult with transcribed text
            
        Raises:
            VoiceError: If transcription fails
        """
        pass
    
    @abstractmethod
    def list_voices(self, language: Optional[str] = None) -> List[VoiceInfo]:
        """
        List available voices.
        
        Args:
            language: Optional language filter
            
        Returns:
            List of VoiceInfo objects
        """
        pass
    
    @abstractmethod
    def get_provider_info(self) -> ProviderInfo:
        """
        Get provider metadata.
        
        Returns:
            ProviderInfo with provider details
        """
        pass
    
    def get_emotion_style(self, emotion: EmotionStyle) -> Dict:
        """
        Get voice style parameters for an emotion.
        
        Args:
            emotion: The emotion to get style for
            
        Returns:
            Dict with style parameters (style, pitch, speed)
        """
        return EMOTION_STYLE_MAPPING.get(emotion, EMOTION_STYLE_MAPPING[EmotionStyle.NEUTRAL])
    
    def supports_language(self, language: str) -> bool:
        """
        Check if provider supports a language.
        
        Args:
            language: Language code (e.g., "en", "zh-CN")
            
        Returns:
            True if language is supported
        """
        provider_info = self.get_provider_info()
        # Check exact match or language family
        if language in provider_info.supported_languages:
            return True
        # Check language family (e.g., "zh" matches "zh-CN")
        lang_code = language.split("-")[0]
        return any(
            lang.startswith(lang_code)
            for lang in provider_info.supported_languages
        )
    
    def validate_text_length(self, text: str) -> bool:
        """
        Validate text length is within provider limits.
        
        Args:
            text: Text to validate
            
        Returns:
            True if within limits
        """
        return len(text) <= self.get_provider_info().max_text_length


class VoiceError(Exception):
    """Exception raised for voice service errors."""
    
    def __init__(self, message: str, provider: str = "", code: str = ""):
        super().__init__(message)
        self.provider = provider
        self.code = code


class AuthenticationError(VoiceError):
    """Authentication failed."""
    pass


class RateLimitError(VoiceError):
    """Rate limit exceeded."""
    pass


class UnsupportedLanguageError(VoiceError):
    """Language not supported by provider."""
    pass


class TextTooLongError(VoiceError):
    """Text exceeds provider limits."""
    pass

# Local Whisper Provider
"""
Local Whisper STT Adapter

Uses local Whisper model for speech-to-text transcription.
- Zero API costs
- Low latency (no network round-trip)
- Offline capable
- Requires whisper package as optional dependency
"""

import os
from typing import Dict, List, Optional
import logging

from ..base import (
    VoiceProvider,
    VoiceInfo,
    ProviderInfo,
    TTSOptions,
    STTOptions,
    TTSResult,
    STTResult,
    VoiceError,
)

logger = logging.getLogger(__name__)

# Supported languages by Whisper
WHISPER_LANGUAGES = [
    "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr", "pl",
    "ca", "nl", "ar", "sv", "it", "id", "hi", "fi", "vi", "he", "uk",
    "el", "ms", "cs", "ro", "da", "hu", "ta", "th", "ur", "bg", "lt",
    "sk", "is", "bn", "ml", "et", "mr", "te", "fa", "sw", "gu", "ml",
]

# Default whisper voices (model sizes)
WHISPER_MODELS = [
    VoiceInfo(voice_id="tiny", name="Whisper Tiny", language="multilingual", gender="neutral", style="fast", provider="local_whisper"),
    VoiceInfo(voice_id="base", name="Whisper Base", language="multilingual", gender="neutral", style="balanced", provider="local_whisper"),
    VoiceInfo(voice_id="small", name="Whisper Small", language="multilingual", gender="neutral", style="accurate", provider="local_whisper"),
    VoiceInfo(voice_id="medium", name="Whisper Medium", language="multilingual", gender="neutral", style="high-accuracy", provider="local_whisper"),
    VoiceInfo(voice_id="large", name="Whisper Large", language="multilingual", gender="neutral", style="best-accuracy", provider="local_whisper"),
]


class LocalWhisperProvider(VoiceProvider):
    """
    Local Whisper STT provider.
    
    Uses OpenAI's Whisper model locally for speech-to-text.
    Supports multiple model sizes for different accuracy/speed tradeoffs.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Local Whisper provider.
        
        Config options:
        - model_size: Model size (tiny/base/small/medium/large)
        - device: Device to use (cpu/cuda)
        - model_dir: Directory to cache models
        """
        super().__init__(config)
        self.model_size = self.config.get("model_size", "base")
        self.device = self.config.get("device", "cpu")
        self.model_dir = self.config.get("model_dir")
        
        # Will be loaded lazily
        self._model = None
        self._available = None
    
    def _check_availability(self) -> bool:
        """Check if whisper package is available."""
        if self._available is None:
            try:
                import whisper
                self._available = True
            except ImportError:
                logger.warning("Whisper package not installed. Install with: pip install openai-whisper")
                self._available = False
        return self._available
    
    def _load_model(self):
        """Load Whisper model lazily."""
        if self._model is None:
            if not self._check_availability():
                raise VoiceError("Whisper package not installed", provider="local_whisper")
            
            import whisper
            
            logger.info(f"Loading Whisper model: {self.model_size}")
            self._model = whisper.load_model(
                self.model_size,
                device=self.device,
                download_root=self.model_dir,
            )
            logger.info(f"Whisper model loaded: {self.model_size}")
    
    def get_provider_info(self) -> ProviderInfo:
        """Get provider information."""
        return ProviderInfo(
            name="local_whisper",
            supported_languages=WHISPER_LANGUAGES,
            max_text_length=100000,  # No API limit
            supports_emotion=False,
            supports_streaming=False,
            pricing={
                "stt_per_second": 0.0,  # Free, local processing
            },
            provider_type="local",
        )
    
    def list_voices(self, language: Optional[str] = None) -> List[VoiceInfo]:
        """
        List available model sizes.
        """
        if not language:
            return WHISPER_MODELS
        
        return [v for v in WHISPER_MODELS if v.language == "multilingual" or v.language.startswith(language.split("-")[0])]
    
    async def text_to_speech(
        self,
        text: str,
        options: TTSOptions,
    ) -> TTSResult:
        """
        Local Whisper does not support TTS.
        """
        raise VoiceError(
            "Local Whisper provider does not support TTS",
            provider="local_whisper",
            code="TTS_NOT_SUPPORTED"
        )
    
    async def text_to_speech_stream(
        self,
        text: str,
        options: TTSOptions,
    ) -> None:
        """
        Local Whisper does not support TTS.
        """
        raise VoiceError(
            "Local Whisper provider does not support TTS",
            provider="local_whisper",
            code="TTS_NOT_SUPPORTED"
        )
    
    async def speech_to_text(
        self,
        audio_data: bytes,
        options: STTOptions,
    ) -> STTResult:
        """
        Convert speech to text using local Whisper model.
        
        Args:
            audio_data: Audio data to transcribe
            options: STT options
            
        Returns:
            STTResult with transcribed text
        """
        if not self._check_availability():
            raise VoiceError("Whisper package not installed", provider="local_whisper")
        
        # Load model if not already loaded
        self._load_model()
        
        # Write audio to temp file (Whisper expects file path)
        import tempfile
        import numpy as np
        
        # Check audio duration
        # Assuming mp3/wav format, estimate duration
        estimated_duration = len(audio_data) / 24000  # Rough estimate
        
        if estimated_duration > options.max_duration_seconds:
            raise VoiceError(
                f"Audio duration {estimated_duration:.1f}s exceeds maximum {options.max_duration_seconds}s",
                provider="local_whisper",
                code="AUDIO_TOO_LONG"
            )
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_data)
            audio_path = f.name
        
        try:
            # Transcribe
            import whisper
            
            result = self._model.transcribe(
                audio_path,
                language=options.language if options.language != "en" else None,
                fp16=self.device == "cuda",
            )
            
            return STTResult(
                text=result.get("text", ""),
                confidence=result.get("confidence", 0.95),
                language=options.language or "en",
                provider="local_whisper",
                duration_seconds=result.get("duration", estimated_duration),
            )
        finally:
            # Clean up temp file
            try:
                os.unlink(audio_path)
            except Exception:
                pass

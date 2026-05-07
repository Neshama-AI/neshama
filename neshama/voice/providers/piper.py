# Piper TTS Provider
"""
Local Piper TTS Adapter

Uses Piper TTS for text-to-speech synthesis locally.
- Zero API costs
- Low latency
- Offline capable
- Lightweight, CPU-friendly
- Requires piper-tts package as optional dependency
"""

import os
import subprocess
import json
from typing import Dict, List, Optional, AsyncIterator
import logging
import tempfile
import struct

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
)

logger = logging.getLogger(__name__)

# Piper TTS supported languages
PIPER_LANGUAGES = [
    "en", "de", "es", "fr", "it", "nl", "pl", "pt", "ru", "uk", "ar", "zh",
]

# Sample Piper voices
PIPER_VOICES = [
    VoiceInfo(voice_id="en_US-lessac-medium", name="Lessac (Medium)", language="en", gender="male", style="neutral", provider="piper"),
    VoiceInfo(voice_id="en_US-lessac-low", name="Lessac (Low)", language="en", gender="male", style="deep", provider="piper"),
    VoiceInfo(voice_id="en_US-amy-medium", name="Amy (Medium)", language="en", gender="female", style="neutral", provider="piper"),
    VoiceInfo(voice_id="en_US-kathleen-low", name="Kathleen (Low)", language="en", gender="female", style="calm", provider="piper"),
    VoiceInfo(voice_id="de_DE-thorsten-medium", name="Thorsten (Medium)", language="de", gender="male", style="neutral", provider="piper"),
    VoiceInfo(voice_id="es_ES-carlos-medium", name="Carlos (Medium)", language="es", gender="male", style="neutral", provider="piper"),
    VoiceInfo(voice_id="fr_FR-siwis-medium", name="Siwis (Medium)", language="fr", gender="female", style="neutral", provider="piper"),
    VoiceInfo(voice_id="it_IT-riccardo-low", name="Riccardo (Low)", language="it", gender="male", style="calm", provider="piper"),
]

# Emotion to speed adjustment for Piper
EMOTION_SPEED_MAP: Dict[EmotionStyle, float] = {
    EmotionStyle.JOY: 1.15,
    EmotionStyle.ANGER: 1.1,
    EmotionStyle.SADNESS: 0.85,
    EmotionStyle.FEAR: 1.2,
    EmotionStyle.TRUST: 0.95,
    EmotionStyle.SURPRISE: 1.1,
    EmotionStyle.DISGUST: 1.0,
    EmotionStyle.ANTICIPATION: 1.05,
    EmotionStyle.NEUTRAL: 1.0,
}


class PiperTTSProvider(VoiceProvider):
    """
    Piper TTS provider.
    
    Uses Piper for local text-to-speech synthesis.
    Piper is an open-source neural TTS engine.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Piper TTS provider.
        
        Config options:
        - model_path: Path to Piper model (.onnx file)
        - model_voice: Voice ID to use
        - piper_bin: Path to piper executable (optional)
        - sample_rate: Output sample rate
        """
        super().__init__(config)
        self.model_path = self.config.get("model_path")
        self.model_voice = self.config.get("model_voice", "en_US-lessac-medium")
        self.piper_bin = self.config.get("piper_bin", "piper")
        self.sample_rate = self.config.get("sample_rate", 22050)
        
        self._available = None
    
    def _check_availability(self) -> bool:
        """Check if piper is available."""
        if self._available is None:
            try:
                result = subprocess.run(
                    [self.piper_bin, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                self._available = result.returncode == 0
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning(
                    "Piper TTS not available. Install from: "
                    "https://github.com/rhasspy/piper#installation"
                )
                self._available = False
        return self._available
    
    def get_provider_info(self) -> ProviderInfo:
        """Get provider information."""
        return ProviderInfo(
            name="piper",
            supported_languages=PIPER_LANGUAGES,
            max_text_length=10000,  # No strict limit
            supports_emotion=False,  # Piper doesn't support emotion params
            supports_streaming=False,  # Piper generates full audio
            pricing={
                "tts_per_char": 0.0,  # Free, local processing
            },
            provider_type="local",
        )
    
    def list_voices(self, language: Optional[str] = None) -> List[VoiceInfo]:
        """
        List available voices.
        """
        if not language:
            return PIPER_VOICES
        
        return [v for v in PIPER_VOICES if v.language.startswith(language.split("-")[0])]
    
    def _build_ssml(self, text: str, speed: float = 1.0) -> str:
        """Build simple SSML-like input for piper."""
        # Piper expects plain text, but we can add some markers
        # Note: Piper has limited prosody control
        return text
    
    async def text_to_speech(
        self,
        text: str,
        options: TTSOptions,
    ) -> TTSResult:
        """
        Convert text to speech using Piper TTS.
        
        Args:
            text: Text to synthesize
            options: TTS options
            
        Returns:
            TTSResult with audio data
        """
        if not self._check_availability():
            raise VoiceError("Piper TTS not installed", provider="piper")
        
        # Use model_path if specified, otherwise assume model is in default location
        model = self.model_path or f"/usr/local/share/piper/voice_{options.voice_id}.onnx"
        
        # Build command
        cmd = [
            self.piper_bin,
            "--model", model,
            "--output_file", "-",
        ]
        
        # Piper generates WAV by default, convert to MP3 if needed
        output_format = options.format.lower()
        if output_format == "mp3":
            cmd.extend(["--output_format", "wav"])  # Piper doesn't support mp3 directly
        
        try:
            import asyncio
            
            # Start process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            # Send text
            stdout, stderr = await process.communicate(
                input=text.encode("utf-8"),
                timeout=30,
            )
            
            if process.returncode != 0:
                error = stderr.decode("utf-8", errors="replace")
                raise VoiceError(
                    f"Piper TTS error: {error}",
                    provider="piper"
                )
            
            audio_data = stdout
            
            # Convert WAV to MP3 if needed
            if output_format == "mp3":
                audio_data = self._convert_wav_to_mp3(audio_data)
            
            return TTSResult(
                audio_data=audio_data,
                duration_seconds=len(audio_data) / self.sample_rate,
                format=output_format,
                voice_id=options.voice_id,
                provider="piper",
            )
            
        except asyncio.TimeoutError:
            raise VoiceError("Piper TTS timeout", provider="piper")
        except Exception as e:
            raise VoiceError(f"Piper TTS error: {str(e)}", provider="piper")
    
    async def text_to_speech_stream(
        self,
        text: str,
        options: TTSOptions,
    ) -> AsyncIterator[bytes]:
        """
        Piper does not support streaming.
        """
        # Generate full audio and yield in chunks
        result = await self.text_to_speech(text, options)
        audio_data = result.audio_data
        
        # Yield in chunks
        chunk_size = 8192
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i:i + chunk_size]
    
    async def speech_to_text(
        self,
        audio_data: bytes,
        options: STTOptions,
    ) -> STTResult:
        """
        Piper TTS does not support STT.
        """
        raise VoiceError(
            "Piper TTS provider does not support STT",
            provider="piper",
            code="STT_NOT_SUPPORTED"
        )
    
    def _convert_wav_to_mp3(self, wav_data: bytes) -> bytes:
        """
        Convert WAV audio to MP3.
        This is a placeholder - in production you'd use an actual audio conversion library.
        """
        # Note: This is a simplified implementation
        # In production, you'd use pydub, ffmpeg-python, or similar
        logger.warning("WAV to MP3 conversion not implemented, returning WAV data")
        return wav_data

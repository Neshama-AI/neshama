# Voice Manager - Provider Registry and Auto-Selection
"""
VoiceManager - Manages multiple voice providers.

Features:
- Provider registration
- Provider auto-selection based on task, language, budget
- NPC voice binding
- TTS/STT caching
- Emotion style mapping
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, AsyncIterator, Any
from pathlib import Path
import hashlib
import logging
import os
from datetime import datetime, timedelta

from .base import (
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

# Default voice cache directory
DEFAULT_CACHE_DIR = Path(__file__).parent.parent.parent / "voice_cache"


@dataclass
class NPCVoiceConfig:
    """Voice configuration for an NPC."""
    npc_id: str
    voice_id: str
    provider_name: str
    language: str = "en"
    emotion: Optional[str] = None  # Default emotion for this NPC
    speed: float = 1.0
    pitch: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "npc_id": self.npc_id,
            "voice_id": self.voice_id,
            "provider_name": self.provider_name,
            "language": self.language,
            "emotion": self.emotion,
            "speed": self.speed,
            "pitch": self.pitch,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "NPCVoiceConfig":
        return cls(
            npc_id=data["npc_id"],
            voice_id=data["voice_id"],
            provider_name=data["provider_name"],
            language=data.get("language", "en"),
            emotion=data.get("emotion"),
            speed=data.get("speed", 1.0),
            pitch=data.get("pitch", 1.0),
        )


@dataclass
class CacheEntry:
    """Cache entry for TTS results."""
    audio_data: bytes
    provider: str
    voice_id: str
    emotion: Optional[str]
    created_at: datetime
    hit_count: int = 0
    
    def is_expired(self, ttl_hours: int = 24) -> bool:
        return datetime.now() > self.created_at + timedelta(hours=ttl_hours)


class VoiceManager:
    """
    Central manager for voice services.
    
    Handles:
    - Provider registration
    - Provider auto-selection
    - NPC voice binding
    - TTS/STT caching
    
    Example:
        >>> manager = VoiceManager()
        >>> 
        >>> # Register a provider
        >>> manager.register_provider(elevenlabs_provider)
        >>> 
        >>> # TTS with auto-selection
        >>> audio = await manager.tts("Hello!", npc_id="npc_001")
        >>> 
        >>> # STT with specific provider
        >>> text = await manager.stt(audio_data, language="en", provider_name="openai")
        >>> 
        >>> # Set NPC voice
        >>> manager.set_npc_voice("npc_001", voice_id="rachel", provider="elevenlabs")
    """
    
    _instance: Optional["VoiceManager"] = None
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        cache_ttl_hours: int = 24,
        enable_cache: bool = True,
    ):
        """
        Initialize VoiceManager.
        
        Args:
            cache_dir: Directory for TTS cache
            cache_ttl_hours: Cache TTL in hours
            enable_cache: Whether to enable caching
        """
        self._providers: Dict[str, VoiceProvider] = {}
        self._npc_voices: Dict[str, NPCVoiceConfig] = {}
        self._cache: Dict[str, CacheEntry] = {}
        
        self._cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_ttl_hours = cache_ttl_hours
        self._enable_cache = enable_cache
        
        # Load NPC voice configs if they exist
        self._load_npc_voices()
    
    @classmethod
    def get_instance(cls) -> "VoiceManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    # ── Provider Management ───────────────────────────────────────────────────
    
    def register_provider(self, provider: VoiceProvider, name: Optional[str] = None):
        """
        Register a voice provider.
        
        Args:
            provider: VoiceProvider instance
            name: Optional provider name (defaults to provider's own name)
        """
        provider_name = name or provider.get_provider_info().name
        self._providers[provider_name] = provider
        logger.info(f"Registered voice provider: {provider_name}")
    
    def unregister_provider(self, name: str) -> bool:
        """
        Unregister a voice provider.
        
        Args:
            name: Provider name
            
        Returns:
            True if provider was removed
        """
        if name in self._providers:
            del self._providers[name]
            logger.info(f"Unregistered voice provider: {name}")
            return True
        return False
    
    def get_provider(self, name: str) -> Optional[VoiceProvider]:
        """
        Get a provider by name.
        
        Args:
            name: Provider name
            
        Returns:
            VoiceProvider or None
        """
        return self._providers.get(name)
    
    def list_providers(self) -> List[ProviderInfo]:
        """
        List all registered providers.
        
        Returns:
            List of ProviderInfo objects
        """
        return [p.get_provider_info() for p in self._providers.values()]
    
    # ── NPC Voice Binding ─────────────────────────────────────────────────────
    
    def set_npc_voice(
        self,
        npc_id: str,
        voice_id: str,
        provider_name: str,
        language: str = "en",
        emotion: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 1.0,
    ):
        """
        Set voice configuration for an NPC.
        
        Args:
            npc_id: NPC identifier
            voice_id: Voice ID to use
            provider_name: Provider name
            language: Language code
            emotion: Default emotion
            speed: Speech speed
            pitch: Speech pitch
        """
        config = NPCVoiceConfig(
            npc_id=npc_id,
            voice_id=voice_id,
            provider_name=provider_name,
            language=language,
            emotion=emotion,
            speed=speed,
            pitch=pitch,
        )
        self._npc_voices[npc_id] = config
        self._save_npc_voice(npc_id, config)
        logger.info(f"Set voice for NPC {npc_id}: {voice_id} ({provider_name})")
    
    def get_npc_voice(self, npc_id: str) -> Optional[NPCVoiceConfig]:
        """
        Get voice configuration for an NPC.
        
        Args:
            npc_id: NPC identifier
            
        Returns:
            NPCVoiceConfig or None
        """
        return self._npc_voices.get(npc_id)
    
    def remove_npc_voice(self, npc_id: str) -> bool:
        """
        Remove voice configuration for an NPC.
        
        Args:
            npc_id: NPC identifier
            
        Returns:
            True if config was removed
        """
        if npc_id in self._npc_voices:
            del self._npc_voices[npc_id]
            # Remove from disk
            config_file = self._cache_dir / f"npc_voice_{npc_id}.json"
            if config_file.exists():
                config_file.unlink()
            return True
        return False
    
    def _save_npc_voice(self, npc_id: str, config: NPCVoiceConfig):
        """Save NPC voice config to disk."""
        import json
        config_file = self._cache_dir / f"npc_voice_{npc_id}.json"
        config_file.write_text(json.dumps(config.to_dict(), indent=2))
    
    def _load_npc_voices(self):
        """Load NPC voice configs from disk."""
        import json
        for config_file in self._cache_dir.glob("npc_voice_*.json"):
            try:
                data = json.loads(config_file.read_text())
                config = NPCVoiceConfig.from_dict(data)
                self._npc_voices[config.npc_id] = config
            except Exception as e:
                logger.error(f"Failed to load NPC voice config {config_file}: {e}")
    
    # ── TTS/STT Operations ────────────────────────────────────────────────────
    
    def _generate_cache_key(
        self,
        text: str,
        voice_id: str,
        emotion: Optional[EmotionStyle],
        provider: str,
    ) -> str:
        """Generate cache key for TTS result."""
        key_parts = [
            text,
            voice_id,
            emotion.value if emotion else "none",
            provider,
        ]
        key_str = "|".join(key_parts)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[bytes]:
        """Get TTS result from cache."""
        if not self._enable_cache:
            return None
        
        entry = self._cache.get(cache_key)
        if entry and not entry.is_expired(self._cache_ttl_hours):
            entry.hit_count += 1
            logger.debug(f"Cache hit for key {cache_key[:8]}...")
            return entry.audio_data
        elif entry:
            # Remove expired entry
            del self._cache[cache_key]
        return None
    
    def _save_to_cache(self, cache_key: str, audio_data: bytes, provider: str, voice_id: str, emotion: Optional[EmotionStyle]):
        """Save TTS result to cache."""
        if not self._enable_cache:
            return
        
        self._cache[cache_key] = CacheEntry(
            audio_data=audio_data,
            provider=provider,
            voice_id=voice_id,
            emotion=emotion.value if emotion else None,
            created_at=datetime.now(),
        )
    
    async def tts(
        self,
        text: str,
        npc_id: Optional[str] = None,
        provider_name: Optional[str] = None,
        voice_id: Optional[str] = None,
        language: str = "en",
        emotion: Optional[EmotionStyle] = None,
        stream: bool = False,
    ) -> Any:
        """
        Convert text to speech.
        
        Args:
            text: Text to synthesize
            npc_id: NPC ID (auto-configures voice from NPC config)
            provider_name: Specific provider to use
            voice_id: Specific voice ID
            language: Language code
            emotion: Emotion style
            stream: Whether to return streaming response
            
        Returns:
            TTSResult or AsyncIterator[bytes] if streaming
        """
        # Get NPC voice config if npc_id is provided
        if npc_id and not provider_name and not voice_id:
            npc_config = self.get_npc_voice(npc_id)
            if npc_config:
                provider_name = npc_config.provider_name
                voice_id = npc_config.voice_id
                language = npc_config.language
                if npc_config.emotion and not emotion:
                    try:
                        emotion = EmotionStyle(npc_config.emotion)
                    except ValueError:
                        pass
        
        # Auto-select provider if not specified
        if not provider_name:
            provider = self.auto_select_provider("tts", language)
        else:
            provider = self._providers.get(provider_name)
        
        if not provider:
            raise VoiceError(f"No provider available for TTS", provider=provider_name or "auto")
        
        # Auto-select voice if not specified
        if not voice_id:
            voices = provider.list_voices(language)
            if voices:
                voice_id = voices[0].voice_id
            else:
                raise VoiceError(f"No voice available for language {language}", provider=provider.name)
        
        # Check cache
        cache_key = self._generate_cache_key(text, voice_id, emotion, provider.get_provider_info().name)
        cached_audio = self._get_from_cache(cache_key)
        
        if cached_audio and not stream:
            return TTSResult(
                audio_data=cached_audio,
                duration_seconds=len(cached_audio) / 24000,  # Estimate
                format="mp3",
                voice_id=voice_id,
                provider=provider.get_provider_info().name,
                cached=True,
            )
        
        # Create options
        options = TTSOptions(
            voice_id=voice_id,
            language=language,
            emotion=emotion,
        )
        
        # Perform TTS
        if stream:
            return provider.text_to_speech_stream(text, options)
        else:
            result = await provider.text_to_speech(text, options)
            
            # Cache result
            if result.audio_data:
                self._save_to_cache(cache_key, result.audio_data, provider.get_provider_info().name, voice_id, emotion)
            
            return result
    
    async def stt(
        self,
        audio_data: bytes,
        language: str = "en",
        provider_name: Optional[str] = None,
        max_duration: int = 60,
    ) -> STTResult:
        """
        Convert speech to text.
        
        Args:
            audio_data: Audio data to transcribe
            language: Language code
            provider_name: Specific provider to use
            max_duration: Maximum audio duration in seconds
            
        Returns:
            STTResult with transcribed text
        """
        # Auto-select provider if not specified
        if not provider_name:
            provider = self.auto_select_provider("stt", language)
        else:
            provider = self._providers.get(provider_name)
        
        if not provider:
            raise VoiceError(f"No provider available for STT", provider=provider_name or "auto")
        
        options = STTOptions(
            language=language,
            max_duration_seconds=max_duration,
        )
        
        return await provider.speech_to_text(audio_data, options)
    
    def auto_select_provider(
        self,
        task: str,  # "tts" or "stt"
        language: Optional[str] = None,
        budget: Optional[str] = None,  # "low", "medium", "high"
    ) -> Optional[VoiceProvider]:
        """
        Auto-select the best provider for a task.
        
        Selection criteria (in order):
        1. Supports the task (tts/stt)
        2. Supports the language
        3. Budget preference (if specified)
        4. Streaming support (preferred)
        
        Args:
            task: "tts" or "stt"
            language: Language code
            budget: Budget preference ("low", "medium", "high")
            
        Returns:
            Selected VoiceProvider or None
        """
        candidates = []
        
        for name, provider in self._providers.items():
            info = provider.get_provider_info()
            
            # Check if provider supports the task
            supports_task = (
                (task == "tts" and info.supports_streaming) or
                (task == "stt")  # All providers support STT for this simple check
            )
            
            if not supports_task:
                continue
            
            # Check language support
            if language and not provider.supports_language(language):
                continue
            
            # Score based on budget
            score = 0
            if budget:
                pricing = info.pricing
                if budget == "low":
                    # Prefer local/cheap providers
                    if info.provider_type == "local":
                        score = 100
                    elif pricing.get(f"{task}_per_char", 1) < 0.0001:
                        score = 80
                elif budget == "high":
                    # Prefer premium providers
                    if info.supports_emotion:
                        score = 100
                    elif info.supports_streaming:
                        score = 80
            
            candidates.append((score, provider))
        
        if not candidates:
            return None
        
        # Return highest scoring provider
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    
    def list_voices(
        self,
        provider_name: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Dict[str, List[VoiceInfo]]:
        """
        List voices from providers.
        
        Args:
            provider_name: Specific provider (None for all)
            language: Language filter
            
        Returns:
            Dict mapping provider name to list of VoiceInfo
        """
        result = {}
        
        providers_to_check = (
            {provider_name: self._providers[provider_name]}
            if provider_name and provider_name in self._providers
            else self._providers
        )
        
        for name, provider in providers_to_check.items():
            result[name] = provider.list_voices(language)
        
        return result
    
    def clear_cache(self):
        """Clear the TTS cache."""
        self._cache.clear()
        logger.info("Voice cache cleared")


# Global manager instance
_manager: Optional[VoiceManager] = None


def get_voice_manager() -> VoiceManager:
    """Get the global VoiceManager instance."""
    global _manager
    if _manager is None:
        _manager = VoiceManager()
    return _manager


def set_voice_manager(manager: VoiceManager):
    """Set the global VoiceManager instance (for testing)."""
    global _manager
    _manager = manager

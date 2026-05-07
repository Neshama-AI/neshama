# Tests - Voice Module Base
"""
Tests for VoiceProvider base class and VoiceManager.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List, AsyncIterator

from neshama.voice.base import (
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
    EMOTION_STYLE_MAPPING,
)
from neshama.voice.manager import VoiceManager, NPCVoiceConfig


class MockVoiceProvider(VoiceProvider):
    """Mock provider for testing."""
    
    def __init__(self, config=None):
        super().__init__(config)
        self._voices = [
            VoiceInfo(
                voice_id="mock_voice_1",
                name="Mock Voice 1",
                language="en-US",
                gender="female",
                style="casual",
                provider="mock",
            ),
            VoiceInfo(
                voice_id="mock_voice_2",
                name="Mock Voice 2",
                language="en-US",
                gender="male",
                style="formal",
                provider="mock",
            ),
        ]
    
    async def text_to_speech(self, text: str, options: TTSOptions) -> TTSResult:
        return TTSResult(
            audio_data=b"mock_audio_data",
            duration_seconds=1.0,
            format="mp3",
            voice_id=options.voice_id,
            provider="mock",
        )
    
    async def text_to_speech_stream(
        self, text: str, options: TTSOptions
    ) -> AsyncIterator[bytes]:
        yield b"chunk1"
        yield b"chunk2"
        yield b"chunk3"
    
    async def speech_to_text(self, audio_data: bytes, options: STTOptions) -> STTResult:
        return STTResult(
            text="Mock transcribed text",
            confidence=0.95,
            language=options.language,
            provider="mock",
        )
    
    def list_voices(self, language=None) -> List[VoiceInfo]:
        if not language:
            return self._voices
        return [v for v in self._voices if v.language.startswith(language.split("-")[0])]
    
    def get_provider_info(self) -> ProviderInfo:
        return ProviderInfo(
            name="mock",
            supported_languages=["en", "zh", "es"],
            max_text_length=1000,
            supports_emotion=True,
            supports_streaming=True,
            pricing={"tts_per_char": 0.0001, "stt_per_second": 0.001},
            provider_type="cloud",
        )


# ── VoiceProvider Base Tests ──────────────────────────────────────────────────

class TestVoiceProvider:
    """Test VoiceProvider base class."""
    
    def test_emotion_style_mapping_complete(self):
        """Test that all EmotionStyle values have mappings."""
        for emotion in EmotionStyle:
            assert emotion in EMOTION_STYLE_MAPPING
            mapping = EMOTION_STYLE_MAPPING[emotion]
            assert "style" in mapping
            assert "pitch" in mapping
            assert "speed" in mapping
    
    def test_emotion_style_joy(self):
        """Test JOY emotion mapping."""
        mapping = EMOTION_STYLE_MAPPING[EmotionStyle.JOY]
        assert mapping["style"] == "cheerful"
        assert mapping["pitch"] == "high"
        assert mapping["speed"] == 1.1
    
    def test_emotion_style_sadness(self):
        """Test SADNESS emotion mapping."""
        mapping = EMOTION_STYLE_MAPPING[EmotionStyle.SADNESS]
        assert mapping["style"] == "somber"
        assert mapping["speed"] < 1.0
    
    def test_emotion_style_fear(self):
        """Test FEAR emotion mapping."""
        mapping = EMOTION_STYLE_MAPPING[EmotionStyle.FEAR]
        assert mapping["speed"] > 1.0
    
    def test_get_emotion_style(self):
        """Test provider's get_emotion_style method."""
        provider = MockVoiceProvider()
        
        result = provider.get_emotion_style(EmotionStyle.JOY)
        assert result["style"] == "cheerful"
    
    def test_supports_language_exact(self):
        """Test exact language match."""
        provider = MockVoiceProvider()
        assert provider.supports_language("en")
        assert provider.supports_language("zh")
    
    def test_supports_language_family(self):
        """Test language family matching."""
        provider = MockVoiceProvider()
        assert provider.supports_language("en-US")
        assert provider.supports_language("zh-CN")
    
    def test_validate_text_length(self):
        """Test text length validation."""
        provider = MockVoiceProvider()
        assert provider.validate_text_length("short text")
        assert not provider.validate_text_length("x" * 2000)


# ── VoiceInfo Tests ───────────────────────────────────────────────────────────

class TestVoiceInfo:
    """Test VoiceInfo dataclass."""
    
    def test_voice_info_creation(self):
        """Test creating VoiceInfo."""
        voice = VoiceInfo(
            voice_id="test_voice",
            name="Test Voice",
            language="en-US",
            gender="female",
            style="casual",
        )
        assert voice.voice_id == "test_voice"
        assert voice.name == "Test Voice"
        assert voice.gender == "female"
    
    def test_voice_info_to_dict(self):
        """Test VoiceInfo serialization."""
        voice = VoiceInfo(
            voice_id="test_voice",
            name="Test Voice",
            language="en-US",
            gender="female",
            style="casual",
            preview_url="https://example.com/preview.mp3",
        )
        result = voice.to_dict()
        assert result["voice_id"] == "test_voice"
        assert result["preview_url"] == "https://example.com/preview.mp3"


# ── ProviderInfo Tests ────────────────────────────────────────────────────────

class TestProviderInfo:
    """Test ProviderInfo dataclass."""
    
    def test_provider_info_creation(self):
        """Test creating ProviderInfo."""
        info = ProviderInfo(
            name="test_provider",
            supported_languages=["en", "zh"],
            max_text_length=5000,
            supports_emotion=True,
            supports_streaming=True,
            pricing={"tts_per_char": 0.0001},
        )
        assert info.name == "test_provider"
        assert len(info.supported_languages) == 2
    
    def test_provider_info_to_dict(self):
        """Test ProviderInfo serialization."""
        info = ProviderInfo(
            name="test_provider",
            supported_languages=["en"],
            max_text_length=5000,
            supports_emotion=True,
            supports_streaming=True,
            pricing={},
        )
        result = info.to_dict()
        assert result["supports_emotion"] is True
        assert result["provider_type"] == "cloud"


# ── VoiceManager Tests ────────────────────────────────────────────────────────

class TestVoiceManager:
    """Test VoiceManager."""
    
    @pytest.fixture
    def manager(self, tmp_path):
        """Create a VoiceManager with mock provider."""
        manager = VoiceManager(
            cache_dir=tmp_path / "voice_cache",
            enable_cache=True,
        )
        manager.register_provider(MockVoiceProvider())
        return manager
    
    def test_register_provider(self, manager):
        """Test provider registration."""
        providers = manager.list_providers()
        assert len(providers) >= 1
        assert providers[0].name == "mock"
    
    def test_get_provider(self, manager):
        """Test getting a provider."""
        provider = manager.get_provider("mock")
        assert provider is not None
        assert provider.get_provider_info().name == "mock"
    
    def test_get_nonexistent_provider(self, manager):
        """Test getting a non-existent provider."""
        provider = manager.get_provider("nonexistent")
        assert provider is None
    
    def test_unregister_provider(self, manager):
        """Test provider unregistration."""
        result = manager.unregister_provider("mock")
        assert result is True
        assert manager.get_provider("mock") is None
    
    def test_list_providers(self, manager):
        """Test listing all providers."""
        providers = manager.list_providers()
        assert len(providers) >= 1
        assert all(isinstance(p, ProviderInfo) for p in providers)
    
    def test_set_npc_voice(self, manager):
        """Test setting NPC voice configuration."""
        manager.set_npc_voice(
            npc_id="npc_001",
            voice_id="mock_voice_1",
            provider_name="mock",
            language="en-US",
        )
        
        config = manager.get_npc_voice("npc_001")
        assert config is not None
        assert config.voice_id == "mock_voice_1"
        assert config.provider_name == "mock"
    
    def test_get_npc_voice_not_set(self, manager):
        """Test getting NPC voice that wasn't set."""
        config = manager.get_npc_voice("nonexistent")
        assert config is None
    
    def test_remove_npc_voice(self, manager):
        """Test removing NPC voice configuration."""
        manager.set_npc_voice(
            npc_id="npc_001",
            voice_id="mock_voice_1",
            provider_name="mock",
        )
        
        result = manager.remove_npc_voice("npc_001")
        assert result is True
        assert manager.get_npc_voice("npc_001") is None
    
    @pytest.mark.asyncio
    async def test_tts(self, manager):
        """Test TTS functionality."""
        result = await manager.tts(
            text="Hello, world!",
            provider_name="mock",
            voice_id="mock_voice_1",
        )
        
        assert isinstance(result, TTSResult)
        assert result.audio_data == b"mock_audio_data"
        assert result.provider == "mock"
    
    @pytest.mark.asyncio
    async def test_tts_with_npc_config(self, manager):
        """Test TTS with NPC voice configuration."""
        manager.set_npc_voice(
            npc_id="npc_001",
            voice_id="mock_voice_1",
            provider_name="mock",
        )
        
        result = await manager.tts(
            text="Hello!",
            npc_id="npc_001",
        )
        
        assert result.voice_id == "mock_voice_1"
    
    @pytest.mark.asyncio
    async def test_tts_caching(self, manager):
        """Test TTS caching."""
        text = "Cache test"
        
        # First call
        result1 = await manager.tts(
            text=text,
            provider_name="mock",
            voice_id="mock_voice_1",
        )
        
        # Second call should use cache
        result2 = await manager.tts(
            text=text,
            provider_name="mock",
            voice_id="mock_voice_1",
        )
        
        assert result1.cached is False
        assert result2.cached is True
    
    @pytest.mark.asyncio
    async def test_stt(self, manager):
        """Test STT functionality."""
        result = await manager.stt(
            audio_data=b"mock_audio",
            language="en",
            provider_name="mock",
        )
        
        assert isinstance(result, STTResult)
        assert result.text == "Mock transcribed text"
        assert result.provider == "mock"
    
    def test_auto_select_provider(self, manager):
        """Test automatic provider selection."""
        provider = manager.auto_select_provider("tts", "en")
        assert provider is not None
        assert provider.get_provider_info().name == "mock"
    
    def test_auto_select_provider_no_match(self, manager):
        """Test auto-select with unsupported language."""
        provider = manager.auto_select_provider("tts", "xx")  # Unsupported language
        assert provider is None
    
    def test_list_voices(self, manager):
        """Test listing voices."""
        voices = manager.list_voices(provider_name="mock", language="en")
        assert "mock" in voices
        assert len(voices["mock"]) == 2
    
    def test_clear_cache(self, manager):
        """Test cache clearing."""
        manager.clear_cache()
        # Just verify it doesn't throw


# ── NPCVoiceConfig Tests ──────────────────────────────────────────────────────

class TestNPCVoiceConfig:
    """Test NPCVoiceConfig dataclass."""
    
    def test_creation(self):
        """Test creating NPCVoiceConfig."""
        config = NPCVoiceConfig(
            npc_id="npc_001",
            voice_id="voice_1",
            provider_name="elevenlabs",
            language="en",
            emotion="joy",
        )
        assert config.npc_id == "npc_001"
        assert config.emotion == "joy"
    
    def test_to_dict(self):
        """Test serialization."""
        config = NPCVoiceConfig(
            npc_id="npc_001",
            voice_id="voice_1",
            provider_name="mock",
        )
        result = config.to_dict()
        assert result["npc_id"] == "npc_001"
        assert "voice_id" in result
    
    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "npc_id": "npc_001",
            "voice_id": "voice_1",
            "provider_name": "mock",
            "language": "en",
        }
        config = NPCVoiceConfig.from_dict(data)
        assert config.npc_id == "npc_001"
        assert config.language == "en"


# ── TTS/STT Options Tests ─────────────────────────────────────────────────────

class TestTTSOptions:
    """Test TTSOptions dataclass."""
    
    def test_creation(self):
        """Test creating TTSOptions."""
        options = TTSOptions(
            voice_id="voice_1",
            language="en",
            emotion=EmotionStyle.JOY,
        )
        assert options.voice_id == "voice_1"
        assert options.emotion == EmotionStyle.JOY
    
    def test_to_dict(self):
        """Test serialization."""
        options = TTSOptions(
            voice_id="voice_1",
            emotion=EmotionStyle.JOY,
        )
        result = options.to_dict()
        assert result["emotion"] == "joy"


class TestSTTOptions:
    """Test STTOptions dataclass."""
    
    def test_creation(self):
        """Test creating STTOptions."""
        options = STTOptions(
            language="en",
            max_duration_seconds=30,
        )
        assert options.max_duration_seconds == 30
    
    def test_to_dict(self):
        """Test serialization."""
        options = STTOptions()
        result = options.to_dict()
        assert result["max_duration_seconds"] == 60

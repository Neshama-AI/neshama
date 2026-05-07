# Tests - Piper TTS Provider
"""
Tests for Piper TTS provider adapter.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from neshama.voice.providers.piper import (
    PiperTTSProvider,
    PIPER_VOICES,
    PIPER_LANGUAGES,
    EMOTION_SPEED_MAP as PIPER_EMOTION_MAP,
)
from neshama.voice.base import (
    TTSOptions,
    TTSResult,
    VoiceError,
)


class TestPiperTTSProvider:
    """Test Piper TTS provider."""
    
    @pytest.fixture
    def provider(self):
        """Create a provider."""
        return PiperTTSProvider(config={
            "model_voice": "en_US-lessac-medium",
            "sample_rate": 22050,
        })
    
    @pytest.fixture
    def provider_with_bin(self):
        """Create a provider with piper binary available."""
        provider = PiperTTSProvider(config={
            "model_voice": "en_US-lessac-medium",
            "piper_bin": "/usr/bin/piper",
        })
        # Mock the availability check to return True
        provider._available = True
        return provider
    
    def test_provider_info(self, provider):
        """Test provider information."""
        info = provider.get_provider_info()
        
        assert info.name == "piper"
        assert info.provider_type == "local"
        assert info.supports_emotion is False
        assert info.supports_streaming is False
        assert info.pricing["tts_per_char"] == 0.0  # Free, local
    
    def test_provider_info_languages(self, provider):
        """Test provider supports multiple languages."""
        info = provider.get_provider_info()
        assert "en" in info.supported_languages
        assert "de" in info.supported_languages
        assert "es" in info.supported_languages
    
    def test_list_voices(self, provider):
        """Test listing voices."""
        voices = provider.list_voices()
        assert len(voices) > 0
        
        # Check English voice exists
        english = next((v for v in voices if v.language == "en"), None)
        assert english is not None
    
    def test_list_voices_filtered(self, provider):
        """Test listing voices with language filter."""
        voices = provider.list_voices(language="en")
        assert all(v.language.startswith("en") for v in voices)
    
    def test_build_ssml(self, provider):
        """Test SSML building."""
        ssml = provider._build_ssml("Hello, world!")
        assert ssml == "Hello, world!"  # Piper uses plain text
    
    def test_check_availability_not_installed(self, provider):
        """Test availability check when piper not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            provider._available = None
            assert provider._check_availability() is False
    
    @pytest.mark.asyncio
    async def test_text_to_speech_not_available(self, provider):
        """Test TTS when piper not available."""
        with patch.object(provider, "_check_availability", return_value=False):
            options = TTSOptions(voice_id="en_US-lessac-medium")
            
            with pytest.raises(VoiceError) as exc_info:
                await provider.text_to_speech("Hello", options)
            
            assert "not installed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_speech_to_text_not_supported(self, provider):
        """Test STT raises error as not supported."""
        options = TTSOptions(voice_id="en_US-lessac-medium")
        
        with pytest.raises(VoiceError) as exc_info:
            await provider.speech_to_text(b"audio", options)
        
        assert "does not support STT" in str(exc_info.value)


class TestPiperVoices:
    """Test Piper voice list."""
    
    def test_voices_exist(self):
        """Test that Piper voices are defined."""
        assert len(PIPER_VOICES) > 0
    
    def test_voice_has_required_fields(self):
        """Test all voices have required fields."""
        for voice in PIPER_VOICES:
            assert voice.voice_id
            assert voice.name
            assert voice.language
            assert voice.gender
            assert voice.style
            assert voice.provider == "piper"
    
    def test_multiple_languages(self):
        """Test voices cover multiple languages."""
        languages = set(v.language for v in PIPER_VOICES)
        assert "en" in languages
        assert "de" in languages
        assert "es" in languages
        assert "fr" in languages
        assert "it" in languages


class TestPiperLanguages:
    """Test Piper language list."""
    
    def test_languages_exist(self):
        """Test that languages are defined."""
        assert len(PIPER_LANGUAGES) > 0
    
    def test_common_languages_present(self):
        """Test common languages are present."""
        assert "en" in PIPER_LANGUAGES
        assert "de" in PIPER_LANGUAGES
        assert "es" in PIPER_LANGUAGES
        assert "fr" in PIPER_LANGUAGES
        assert "it" in PIPER_LANGUAGES
        assert "zh" in PIPER_LANGUAGES


class TestPiperEmotionMapping:
    """Test Piper emotion to speed mapping."""
    
    def test_all_emotions_mapped(self):
        """Test all emotions have speed mappings."""
        from neshama.voice.base import EmotionStyle
        for emotion in EmotionStyle:
            assert emotion in PIPER_EMOTION_MAP
    
    def test_joy_faster(self):
        """Test JOY maps to faster speed."""
        from neshama.voice.base import EmotionStyle
        assert PIPER_EMOTION_MAP[EmotionStyle.JOY] == 1.15
    
    def test_sadness_slower(self):
        """Test SADNESS maps to slower speed."""
        from neshama.voice.base import EmotionStyle
        assert PIPER_EMOTION_MAP[EmotionStyle.SADNESS] == 0.85
    
    def test_neutral_normal(self):
        """Test NEUTRAL maps to normal speed."""
        from neshama.voice.base import EmotionStyle
        assert PIPER_EMOTION_MAP[EmotionStyle.NEUTRAL] == 1.0

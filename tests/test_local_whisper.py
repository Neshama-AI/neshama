# Tests - Local Whisper Provider
"""
Tests for Local Whisper STT provider adapter.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from neshama.voice.providers.local_whisper import (
    LocalWhisperProvider,
    WHISPER_MODELS,
    WHISPER_LANGUAGES,
)
from neshama.voice.base import (
    STTOptions,
    STTResult,
    VoiceError,
)


class TestLocalWhisperProvider:
    """Test Local Whisper provider."""
    
    @pytest.fixture
    def provider(self):
        """Create a provider."""
        return LocalWhisperProvider(config={
            "model_size": "base",
            "device": "cpu",
        })
    
    def test_provider_info(self, provider):
        """Test provider information."""
        info = provider.get_provider_info()
        
        assert info.name == "local_whisper"
        assert info.provider_type == "local"
        assert info.supports_emotion is False
        assert info.supports_streaming is False
        assert info.pricing["stt_per_second"] == 0.0  # Free, local
    
    def test_provider_info_languages(self, provider):
        """Test provider supports many languages."""
        info = provider.get_provider_info()
        assert "en" in info.supported_languages
        assert "zh" in info.supported_languages
        assert "es" in info.supported_languages
    
    def test_list_voices_models(self, provider):
        """Test listing model sizes."""
        models = provider.list_voices()
        assert len(models) == 5  # tiny, base, small, medium, large
        
        # Check base model exists
        base = next((m for m in models if m.voice_id == "base"), None)
        assert base is not None
        assert base.name == "Whisper Base"
    
    def test_list_voices_filtered(self, provider):
        """Test listing voices with language filter."""
        models = provider.list_voices(language="en")
        # All models support multilingual
        assert all(m.language == "multilingual" for m in models)
    
    def test_check_availability_not_installed(self, provider):
        """Test availability check when whisper not installed."""
        with patch.dict("sys.modules", {"whisper": None}):
            provider._available = None
            assert provider._check_availability() is False
    
    @pytest.mark.asyncio
    async def test_text_to_speech_not_supported(self, provider):
        """Test TTS raises error as not supported."""
        from neshama.voice.base import TTSOptions
        
        options = TTSOptions(voice_id="base")
        
        with pytest.raises(VoiceError) as exc_info:
            await provider.text_to_speech("Hello", options)
        
        assert "does not support TTS" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_text_to_speech_stream_not_supported(self, provider):
        """Test streaming TTS raises error as not supported."""
        from neshama.voice.base import TTSOptions
        
        options = TTSOptions(voice_id="base")
        
        # The method is async and raises an error
        with pytest.raises(VoiceError) as exc_info:
            await provider.text_to_speech_stream("Hello", options)
        
        assert "does not support TTS" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_speech_to_text_not_available(self, provider):
        """Test STT when whisper not installed."""
        with patch.object(provider, "_check_availability", return_value=False):
            options = STTOptions()
            
            with pytest.raises(VoiceError) as exc_info:
                await provider.speech_to_text(b"mock_audio", options)
            
            assert "not installed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_speech_to_text_too_long(self, provider):
        """Test STT with audio exceeding max duration."""
        with patch.object(provider, "_check_availability", return_value=True):
            with patch.object(provider, "_load_model"):
                options = STTOptions(max_duration_seconds=10)
                # Simulate long audio
                large_audio = b"x" * 1000000  # Large audio
                
                with pytest.raises(VoiceError) as exc_info:
                    await provider.speech_to_text(large_audio, options)
                
                assert "exceeds maximum" in str(exc_info.value)


class TestWhisperModels:
    """Test Whisper model list."""
    
    def test_models_exist(self):
        """Test that Whisper models are defined."""
        assert len(WHISPER_MODELS) == 5
    
    def test_model_has_required_fields(self):
        """Test all models have required fields."""
        for model in WHISPER_MODELS:
            assert model.voice_id
            assert model.name
            assert model.language == "multilingual"
            assert model.provider == "local_whisper"
    
    def test_model_sizes(self):
        """Test all standard model sizes present."""
        sizes = {m.voice_id for m in WHISPER_MODELS}
        expected = {"tiny", "base", "small", "medium", "large"}
        assert sizes == expected


class TestWhisperLanguages:
    """Test Whisper language list."""
    
    def test_languages_exist(self):
        """Test that languages are defined."""
        assert len(WHISPER_LANGUAGES) > 0
    
    def test_common_languages_present(self):
        """Test common languages are present."""
        assert "en" in WHISPER_LANGUAGES
        assert "zh" in WHISPER_LANGUAGES
        assert "es" in WHISPER_LANGUAGES
        assert "fr" in WHISPER_LANGUAGES
        assert "de" in WHISPER_LANGUAGES
        assert "ja" in WHISPER_LANGUAGES
        assert "ko" in WHISPER_LANGUAGES

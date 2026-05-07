# Tests - Voice API
"""
Tests for Voice API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from io import BytesIO

from fastapi.testclient import TestClient
from fastapi import FastAPI

from neshama.voice import VoiceManager, EmotionStyle
from neshama.voice.base import TTSResult, STTResult, VoiceInfo, ProviderInfo
from neshama.voice.manager import set_voice_manager


# Create mock providers for testing
class MockVoiceProvider:
    """Mock provider for API tests."""
    
    def __init__(self):
        self.name = "mock_provider"
        self._voices = [
            VoiceInfo(
                voice_id="mock_voice_1",
                name="Mock Voice 1",
                language="en-US",
                gender="female",
                style="casual",
                provider="mock_provider",
            ),
        ]
    
    def get_provider_info(self):
        return ProviderInfo(
            name="mock_provider",
            supported_languages=["en", "zh"],
            max_text_length=1000,
            supports_emotion=True,
            supports_streaming=True,
            pricing={"tts_per_char": 0.0001},
        )
    
    def list_voices(self, language=None):
        if not language:
            return self._voices
        return [v for v in self._voices if v.language.startswith(language.split("-")[0])]
    
    def supports_language(self, language):
        """Check if provider supports a language."""
        info = self.get_provider_info()
        return language in info.supported_languages
    
    async def text_to_speech(self, text, options):
        return TTSResult(
            audio_data=b"mock_audio_data",
            duration_seconds=1.0,
            format="mp3",
            voice_id=options.voice_id,
            provider="mock_provider",
        )
    
    async def text_to_speech_stream(self, text, options):
        yield b"chunk1"
        yield b"chunk2"
    
    async def speech_to_text(self, audio_data, options):
        return STTResult(
            text="Mock transcribed text",
            confidence=0.95,
            language=options.language,
            provider="mock_provider",
        )


# Create test app
def create_test_app():
    """Create a FastAPI app for testing."""
    from neshama.web.api.voice import router
    
    app = FastAPI()
    app.include_router(router, prefix="/api/voice", tags=["voice"])
    return app


@pytest.fixture
def mock_manager():
    """Create a mock voice manager."""
    manager = VoiceManager()
    manager.register_provider(MockVoiceProvider())
    set_voice_manager(manager)
    return manager


@pytest.fixture
def client(mock_manager):
    """Create test client."""
    app = create_test_app()
    return TestClient(app)


class TestTTSEndpoint:
    """Test TTS endpoint."""
    
    def test_tts_success(self, client):
        """Test successful TTS."""
        response = client.post(
            "/api/voice/tts",
            data={
                "text": "Hello, world!",
                "provider": "mock_provider",
                "voice_id": "mock_voice_1",
                "language": "en",
                "stream": "false",
            },
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
    
    def test_tts_streaming(self, client):
        """Test streaming TTS."""
        response = client.post(
            "/api/voice/tts",
            data={
                "text": "Hello!",
                "provider": "mock_provider",
                "voice_id": "mock_voice_1",
                "stream": "true",
            },
        )
        
        assert response.status_code == 200
        assert response.headers.get("transfer-encoding") == "chunked"
    
    def test_tts_invalid_emotion(self, client):
        """Test TTS with invalid emotion."""
        response = client.post(
            "/api/voice/tts",
            data={
                "text": "Hello!",
                "provider": "mock_provider",
                "emotion": "invalid_emotion",
            },
        )
        
        assert response.status_code == 400
        assert "Invalid emotion" in response.json()["detail"]
    
    def test_tts_with_emotion(self, client):
        """Test TTS with emotion."""
        response = client.post(
            "/api/voice/tts",
            data={
                "text": "Hello!",
                "provider": "mock_provider",
                "voice_id": "mock_voice_1",
                "emotion": "joy",
            },
        )
        
        assert response.status_code == 200


class TestSTTEndpoint:
    """Test STT endpoint."""
    
    def test_stt_success(self, client):
        """Test successful STT."""
        # Create mock audio file
        audio_data = b"mock_audio_data"
        
        response = client.post(
            "/api/voice/stt",
            files={"audio_file": ("test.mp3", BytesIO(audio_data), "audio/mpeg")},
            data={
                "language": "en",
                "provider": "mock_provider",
            },
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "text" in result["data"]
    
    def test_stt_no_provider(self, client):
        """Test STT without specific provider."""
        audio_data = b"mock_audio_data"
        
        response = client.post(
            "/api/voice/stt",
            files={"audio_file": ("test.mp3", BytesIO(audio_data), "audio/mpeg")},
            data={"language": "en"},
        )
        
        # Should use auto-selection
        assert response.status_code == 200


class TestProviderEndpoints:
    """Test provider listing endpoints."""
    
    def test_list_providers(self, client):
        """Test listing all providers."""
        response = client.get("/api/voice/providers")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "providers" in result["data"]
        assert result["data"]["count"] >= 1
    
    def test_list_provider_voices(self, client):
        """Test listing voices for a provider."""
        response = client.get("/api/voice/voices/mock_provider")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "voices" in result["data"]
        assert len(result["data"]["voices"]) > 0
    
    def test_list_provider_voices_with_filter(self, client):
        """Test listing voices with language filter."""
        response = client.get("/api/voice/voices/mock_provider?language=en")
        
        assert response.status_code == 200
        result = response.json()
        assert all(v["language"].startswith("en") for v in result["data"]["voices"])
    
    def test_list_nonexistent_provider(self, client):
        """Test listing voices for non-existent provider."""
        response = client.get("/api/voice/voices/nonexistent")
        
        assert response.status_code == 404


class TestNPCVoiceEndpoints:
    """Test NPC voice binding endpoints."""
    
    def test_set_npc_voice(self, client):
        """Test setting NPC voice configuration."""
        response = client.post(
            "/api/voice/npc/test_npc_001/voice",
            data={
                "voice_id": "mock_voice_1",
                "provider": "mock_provider",
                "language": "en",
            },
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["npc_id"] == "test_npc_001"
    
    def test_set_npc_voice_with_emotion(self, client):
        """Test setting NPC voice with emotion."""
        response = client.post(
            "/api/voice/npc/test_npc_002/voice",
            data={
                "voice_id": "mock_voice_1",
                "provider": "mock_provider",
                "emotion": "joy",
            },
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["data"]["emotion"] == "joy"
    
    def test_set_npc_voice_invalid_provider(self, client):
        """Test setting NPC voice with invalid provider."""
        response = client.post(
            "/api/voice/npc/test_npc/voice",
            data={
                "voice_id": "mock_voice_1",
                "provider": "nonexistent_provider",
            },
        )
        
        assert response.status_code == 404
    
    def test_get_npc_voice(self, client):
        """Test getting NPC voice configuration."""
        # First set the voice
        client.post(
            "/api/voice/npc/test_npc_003/voice",
            data={
                "voice_id": "mock_voice_1",
                "provider": "mock_provider",
            },
        )
        
        # Then get it
        response = client.get("/api/voice/npc/test_npc_003/voice")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["npc_id"] == "test_npc_003"
    
    def test_get_npc_voice_not_set(self, client):
        """Test getting NPC voice that wasn't set."""
        response = client.get("/api/voice/npc/nonexistent_npc/voice")
        
        assert response.status_code == 200
        result = response.json()
        assert result["data"] is None
    
    def test_delete_npc_voice(self, client):
        """Test deleting NPC voice configuration."""
        # First set the voice
        client.post(
            "/api/voice/npc/test_npc_004/voice",
            data={
                "voice_id": "mock_voice_1",
                "provider": "mock_provider",
            },
        )
        
        # Then delete it
        response = client.delete("/api/voice/npc/test_npc_004/voice")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True


class TestCacheEndpoint:
    """Test cache endpoint."""
    
    def test_clear_cache(self, client):
        """Test clearing cache."""
        response = client.delete("/api/voice/cache")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert "cleared" in result["message"]

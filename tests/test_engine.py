"""
Neshama Engine Tests

Tests for NeshamaEngine and ConversationManager.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.core.engine import NeshamaEngine, EngineConfig, ChatResponse
from neshama.core.conversation import ConversationManager, Session, Message


class TestConversationManager:
    """Tests for ConversationManager."""
    
    def test_initialization(self):
        """Test manager initialization."""
        manager = ConversationManager()
        assert manager is not None
        assert manager.session_count == 0
    
    def test_create_session(self):
        """Test session creation."""
        manager = ConversationManager()
        session = manager.create_session(user_id="test_user")
        assert session is not None
        assert session.user_id == "test_user"
        assert manager.session_count == 1
    
    def test_add_message(self):
        """Test adding messages."""
        manager = ConversationManager()
        session = manager.create_session()
        
        success = manager.add_message(session.id, "user", "Hello")
        assert success is True
        
        history = manager.get_history(session.id)
        assert len(history) == 1
        assert history[0]["content"] == "Hello"
    
    def test_get_context(self):
        """Test context retrieval."""
        manager = ConversationManager()
        session = manager.create_session()
        
        manager.add_message(session.id, "user", "Hello")
        manager.add_message(session.id, "assistant", "Hi!")
        
        context = manager.get_context(session.id)
        assert "Hello" in context
        assert "Hi!" in context
    
    def test_delete_session(self):
        """Test session deletion."""
        manager = ConversationManager()
        session = manager.create_session()
        
        assert manager.session_count == 1
        
        success = manager.delete_session(session.id)
        assert success is True
        assert manager.session_count == 0


class TestSession:
    """Tests for Session."""
    
    def test_initialization(self):
        """Test session initialization."""
        session = Session()
        assert session.id is not None
        assert len(session.messages) == 0
    
    def test_add_message(self):
        """Test adding messages."""
        session = Session()
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi!")
        
        assert len(session.messages) == 2
    
    def test_get_history(self):
        """Test history retrieval."""
        session = Session()
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi!")
        
        history = session.get_history()
        assert len(history) == 2


class TestNeshamaEngine:
    """Tests for NeshamaEngine."""
    
    def test_initialization(self):
        """Test engine initialization."""
        config = EngineConfig(
            engine_id="test",
            model_provider="mock",
        )
        engine = NeshamaEngine(config)
        assert engine is not None
    
    def test_create_session(self):
        """Test session creation."""
        engine = NeshamaEngine()
        session = engine.create_session(user_id="test_user")
        assert session is not None
    
    def test_chat(self):
        """Test chat functionality."""
        engine = NeshamaEngine()
        session = engine.create_session()
        
        response = engine.chat("Hello!", session_id=session.id)
        assert response is not None
        assert isinstance(response, ChatResponse)
        assert len(response.content) > 0
    
    def test_chat_multi_turn(self):
        """Test multi-turn conversation."""
        engine = NeshamaEngine()
        session = engine.create_session()
        
        response1 = engine.chat("Hello!", session_id=session.id)
        response2 = engine.chat("How are you?", session_id=session.id)
        
        assert response1.content != response2.content


class TestEngineConfig:
    """Tests for EngineConfig."""
    
    def test_defaults(self):
        """Test default configuration."""
        config = EngineConfig()
        assert config.engine_id == "default"
        assert config.engine_name == "Neshama"
        assert config.model_provider == "mock"
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = EngineConfig(
            engine_id="custom",
            soul_enabled=False,
            memory_enabled=False,
        )
        assert config.engine_id == "custom"
        assert config.soul_enabled is False
        assert config.memory_enabled is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

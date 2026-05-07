"""
Neshama WebSocket Tests
"""

import pytest
import sys
import os
import asyncio
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.web.api.ws import (
    ConnectionManager,
    WebSocketMessage,
    MessageType,
    get_connection_manager,
    broadcast_emotion_change,
)


class TestWebSocketMessage:
    """Tests for WebSocketMessage."""

    def test_to_json(self):
        """Test message serialization."""
        msg = WebSocketMessage(
            type=MessageType.EMOTION_CHANGED,
            session_id="session_001",
            npc_id="npc_001",
            data={"joy": 0.8},
        )
        
        json_str = msg.to_json()
        data = json.loads(json_str)
        
        assert data["type"] == "emotion_changed"
        assert data["session_id"] == "session_001"
        assert data["npc_id"] == "npc_001"
        assert data["data"]["joy"] == 0.8

    def test_from_json(self):
        """Test message deserialization."""
        json_str = json.dumps({
            "type": "behavior_triggered",
            "session_id": "session_001",
            "npc_id": "npc_001",
            "data": {"emotion": "anger"},
            "timestamp": "2024-01-01T00:00:00",
            "message_id": "msg_001",
        })
        
        msg = WebSocketMessage.from_json(json_str)
        
        assert msg.type == MessageType.BEHAVIOR_TRIGGERED
        assert msg.session_id == "session_001"
        assert msg.npc_id == "npc_001"

    def test_message_id_generated(self):
        """Test that message ID is generated."""
        msg = WebSocketMessage(
            type=MessageType.CONNECTED,
            session_id="session_001",
        )
        
        assert msg.message_id is not None
        assert len(msg.message_id) > 0

    def test_timestamp_generated(self):
        """Test that timestamp is generated."""
        msg = WebSocketMessage(
            type=MessageType.CONNECTED,
            session_id="session_001",
        )
        
        assert msg.timestamp is not None


class TestConnectionManagerInit:
    """Tests for ConnectionManager initialization."""

    def test_default_init(self):
        """Test default initialization."""
        manager = ConnectionManager()
        
        assert manager is not None
        assert len(manager._session_connections) == 0
        assert len(manager._npc_subscriptions) == 0


class TestConnectionManagerConnect:
    """Tests for WebSocket connection."""

    def test_connect_creates_session(self):
        """Test that connect initializes session dict."""
        manager = ConnectionManager()
        
        # Can't actually connect without a real websocket, but we can check the structure
        assert len(manager._session_connections) == 0


class TestMessageType:
    """Tests for MessageType enum."""

    def test_all_message_types_exist(self):
        """Test that all expected message types exist."""
        expected_types = [
            "emotion_changed",
            "behavior_triggered",
            "relation_updated",
            "npc_chat",
            "session_heartbeat",
            "error",
            "connected",
            "ping",
            "pong",
        ]
        
        for type_str in expected_types:
            msg_type = MessageType(type_str)
            assert msg_type.value == type_str

    def test_message_type_values(self):
        """Test message type string values."""
        assert MessageType.EMOTION_CHANGED.value == "emotion_changed"
        assert MessageType.BEHAVIOR_TRIGGERED.value == "behavior_triggered"
        assert MessageType.CONNECTED.value == "connected"


class TestGetConnectionManager:
    """Tests for global connection manager."""

    def test_get_connection_manager(self):
        """Test getting global connection manager."""
        manager = get_connection_manager()
        
        assert manager is not None
        assert isinstance(manager, ConnectionManager)

    def test_get_connection_manager_singleton(self):
        """Test that get_connection_manager returns singleton."""
        manager1 = get_connection_manager()
        manager2 = get_connection_manager()
        
        assert manager1 is manager2


class TestConnectionStats:
    """Tests for connection statistics."""

    def test_get_stats(self):
        """Test getting connection stats."""
        manager = ConnectionManager()
        
        stats = manager.get_stats()
        
        assert "total_sessions" in stats
        assert "total_connections" in stats
        assert "subscribed_npcs" in stats
        assert stats["total_sessions"] == 0


class TestBroadcastHelpers:
    """Tests for broadcast helper functions."""

    @pytest.mark.asyncio
    async def test_broadcast_emotion_change(self):
        """Test broadcast emotion change function."""
        # This would require a real websocket to fully test
        # Just verify the function exists and is callable
        assert callable(broadcast_emotion_change)


class TestWebSocketMessageData:
    """Tests for WebSocketMessage data handling."""

    def test_data_can_be_none(self):
        """Test that data can be None."""
        msg = WebSocketMessage(
            type=MessageType.PONG,
            session_id="session_001",
            data=None,
        )
        
        json_str = msg.to_json()
        data = json.loads(json_str)
        
        assert data["data"] is None

    def test_data_with_nested_dict(self):
        """Test data with nested dictionary."""
        msg = WebSocketMessage(
            type=MessageType.EMOTION_CHANGED,
            session_id="session_001",
            data={
                "changes": {"joy": 0.5, "anger": -0.3},
                "current_state": {"joy": 0.8, "anger": 0.2},
            },
        )
        
        json_str = msg.to_json()
        data = json.loads(json_str)
        
        assert data["data"]["changes"]["joy"] == 0.5
        assert data["data"]["current_state"]["anger"] == 0.2

    def test_data_with_list(self):
        """Test data with list."""
        msg = WebSocketMessage(
            type=MessageType.BEHAVIOR_TRIGGERED,
            session_id="session_001",
            data={
                "triggers": [
                    {"emotion": "anger", "threshold": 0.7},
                    {"emotion": "joy", "threshold": 0.5},
                ]
            },
        )
        
        json_str = msg.to_json()
        data = json.loads(json_str)
        
        assert len(data["data"]["triggers"]) == 2


class TestMessageTypeEnum:
    """Tests for MessageType enum operations."""

    def test_enum_from_string(self):
        """Test creating enum from string."""
        msg_type = MessageType("emotion_changed")
        
        assert msg_type == MessageType.EMOTION_CHANGED

    def test_enum_invalid_type(self):
        """Test invalid message type."""
        with pytest.raises(ValueError):
            MessageType("invalid_type")


class TestUnicodeHandling:
    """Tests for unicode handling in messages."""

    def test_unicode_in_data(self):
        """Test unicode in message data."""
        msg = WebSocketMessage(
            type=MessageType.NPC_CHAT,
            session_id="session_001",
            data={"message": "你好世界 🌍"},
        )
        
        json_str = msg.to_json()
        
        # Should not raise
        assert json_str is not None
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        assert "你好世界" in parsed["data"]["message"]

    def test_unicode_in_npc_id(self):
        """Test unicode in NPC ID."""
        msg = WebSocketMessage(
            type=MessageType.EMOTION_CHANGED,
            session_id="session_001",
            npc_id="npc_你好",
        )
        
        json_str = msg.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["npc_id"] == "npc_你好"


class TestSessionConnectionCount:
    """Tests for session connection counting."""

    def test_get_session_connection_count_empty(self):
        """Test getting count for empty session."""
        manager = ConnectionManager()
        
        count = manager.get_session_connection_count("nonexistent")
        
        assert count == 0


class TestAsyncHelpers:
    """Tests for async helper functions."""

    @pytest.mark.asyncio
    async def test_broadcast_functions_exist(self):
        """Test that broadcast functions exist."""
        from neshama.web.api.ws import (
            broadcast_behavior_trigger,
            broadcast_relation_update,
        )
        
        assert callable(broadcast_behavior_trigger)
        assert callable(broadcast_relation_update)

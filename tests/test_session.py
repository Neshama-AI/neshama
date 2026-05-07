"""
Neshama Session Management Tests
"""

import pytest
import sys
import os
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.web.api.session import (
    SessionManager,
    Session,
    NPCRegistration,
    get_session_manager,
)


class TestSessionManagerInit:
    """Tests for SessionManager initialization."""

    def test_default_init(self):
        """Test default initialization."""
        manager = SessionManager()
        assert manager is not None
        assert len(manager._sessions) == 0
        assert manager._session_timeout == 300

    def test_custom_timeout(self):
        """Test initialization with custom timeout."""
        manager = SessionManager(session_timeout=60)
        assert manager._session_timeout == 60


class TestSessionCreation:
    """Tests for session creation."""

    def test_create_session(self):
        """Test creating a session."""
        manager = SessionManager()
        
        session = manager.create_session("game_001", "client_abc")
        
        assert session is not None
        assert session.game_id == "game_001"
        assert session.client_id == "client_abc"
        assert session.session_id is not None
        assert len(session.session_id) > 0

    def test_create_session_with_metadata(self):
        """Test creating a session with metadata."""
        manager = SessionManager()
        
        metadata = {"version": "1.0", "mode": "test"}
        session = manager.create_session("game_001", "client_abc", metadata)
        
        assert session.metadata == metadata

    def test_session_has_timestamps(self):
        """Test that session has timestamps."""
        manager = SessionManager()
        
        session = manager.create_session("game_001", "client_abc")
        
        assert session.created_at is not None
        assert session.last_heartbeat is not None


class TestSessionRetrieval:
    """Tests for session retrieval."""

    def test_get_session(self):
        """Test getting a session by ID."""
        manager = SessionManager()
        
        created = manager.create_session("game_001", "client_abc")
        retrieved = manager.get_session(created.session_id)
        
        assert retrieved is not None
        assert retrieved.session_id == created.session_id

    def test_get_nonexistent_session(self):
        """Test getting a nonexistent session."""
        manager = SessionManager()
        
        session = manager.get_session("nonexistent_id")
        
        assert session is None

    def test_get_client_sessions(self):
        """Test getting all sessions for a client."""
        manager = SessionManager()
        
        manager.create_session("game_001", "client_abc")
        manager.create_session("game_002", "client_abc")
        manager.create_session("game_003", "client_xyz")
        
        sessions = manager.get_client_sessions("client_abc")
        
        assert len(sessions) == 2


class TestNPCRegistration:
    """Tests for NPC registration."""

    def test_register_npc(self):
        """Test registering an NPC to a session."""
        manager = SessionManager()
        
        session = manager.create_session("game_001", "client_abc")
        registration = manager.register_npc("npc_001", session.session_id)
        
        assert registration is not None
        assert registration.npc_id == "npc_001"
        assert registration.session_id == session.session_id

    def test_register_npc_to_nonexistent_session(self):
        """Test registering NPC to nonexistent session."""
        manager = SessionManager()
        
        registration = manager.register_npc("npc_001", "nonexistent_session")
        
        assert registration is None

    def test_register_same_npc_twice(self):
        """Test registering same NPC updates registration."""
        manager = SessionManager()
        
        session1 = manager.create_session("game_001", "client_abc")
        session2 = manager.create_session("game_002", "client_xyz")
        
        manager.register_npc("npc_001", session1.session_id)
        manager.register_npc("npc_001", session2.session_id)
        
        npcs = manager.get_session_npcs(session2.session_id)
        
        assert "npc_001" in npcs

    def test_unregister_npc(self):
        """Test unregistering an NPC."""
        manager = SessionManager()
        
        session = manager.create_session("game_001", "client_abc")
        manager.register_npc("npc_001", session.session_id)
        
        result = manager.unregister_npc("npc_001")
        
        assert result is True
        
        npcs = manager.get_session_npcs(session.session_id)
        assert "npc_001" not in npcs

    def test_unregister_nonexistent_npc(self):
        """Test unregistering nonexistent NPC."""
        manager = SessionManager()
        
        result = manager.unregister_npc("nonexistent_npc")
        
        assert result is False

    def test_get_npc_session(self):
        """Test getting NPC's session."""
        manager = SessionManager()
        
        session = manager.create_session("game_001", "client_abc")
        manager.register_npc("npc_001", session.session_id)
        
        session_id = manager.get_npc_session("npc_001")
        
        assert session_id == session.session_id

    def test_get_npc_session_nonexistent(self):
        """Test getting session for nonexistent NPC."""
        manager = SessionManager()
        
        session_id = manager.get_npc_session("nonexistent_npc")
        
        assert session_id is None


class TestHeartbeat:
    """Tests for heartbeat functionality."""

    def test_heartbeat_updates_timestamp(self):
        """Test that heartbeat updates timestamp."""
        manager = SessionManager()
        
        session = manager.create_session("game_001", "client_abc")
        original_heartbeat = session.last_heartbeat
        
        time.sleep(0.01)  # Small delay
        
        result = manager.heartbeat(session.session_id)
        
        assert result is True
        
        updated = manager.get_session(session.session_id)
        assert updated.last_heartbeat != original_heartbeat

    def test_heartbeat_nonexistent_session(self):
        """Test heartbeat for nonexistent session."""
        manager = SessionManager()
        
        result = manager.heartbeat("nonexistent_session")
        
        assert result is False


class TestSessionLifecycle:
    """Tests for session lifecycle."""

    def test_is_alive_within_timeout(self):
        """Test session is alive within timeout."""
        manager = SessionManager()
        
        session = manager.create_session("game_001", "client_abc")
        
        assert session.is_alive(timeout_seconds=300) is True

    def test_is_alive_after_timeout(self):
        """Test session is not alive after timeout."""
        manager = SessionManager()
        
        session = manager.create_session("game_001", "client_abc")
        session.last_heartbeat = (datetime.now() - timedelta(seconds=400)).isoformat()
        
        assert session.is_alive(timeout_seconds=300) is False

    def test_get_active_sessions(self):
        """Test getting active sessions."""
        manager = SessionManager()
        
        session1 = manager.create_session("game_001", "client_abc")
        session2 = manager.create_session("game_002", "client_xyz")
        
        # Make one session expired
        session2.last_heartbeat = (datetime.now() - timedelta(seconds=400)).isoformat()
        
        active = manager.get_active_sessions()
        
        assert len(active) == 1
        assert active[0].session_id == session1.session_id

    def test_cleanup_expired(self):
        """Test cleaning up expired sessions."""
        manager = SessionManager()
        
        session1 = manager.create_session("game_001", "client_abc")
        session2 = manager.create_session("game_002", "client_xyz")
        
        # Make one session expired
        session2.last_heartbeat = (datetime.now() - timedelta(seconds=400)).isoformat()
        
        removed = manager.cleanup_expired()
        
        assert removed == 1
        
        # Verify
        active = manager.get_active_sessions()
        assert len(active) == 1


class TestSessionStats:
    """Tests for session statistics."""

    def test_get_stats(self):
        """Test getting session manager stats."""
        manager = SessionManager()
        
        manager.create_session("game_001", "client_abc")
        session = manager.create_session("game_002", "client_xyz")
        manager.register_npc("npc_001", session.session_id)
        
        stats = manager.get_stats()
        
        assert stats["total_sessions"] == 2
        assert stats["active_sessions"] == 2
        assert stats["active_npcs"] == 1


class TestSessionSerialization:
    """Tests for session serialization."""

    def test_session_to_dict(self):
        """Test Session serialization."""
        manager = SessionManager()
        
        session = manager.create_session("game_001", "client_abc")
        manager.register_npc("npc_001", session.session_id)
        
        # Use manager method to get session with NPC count
        data = manager.get_session_with_npc_count(session.session_id)
        
        assert data["session_id"] == session.session_id
        assert data["game_id"] == "game_001"
        assert data["client_id"] == "client_abc"
        assert data["npc_count"] == 1
        assert "is_alive" in data

    def test_registration_to_dict(self):
        """Test NPCRegistration serialization."""
        manager = SessionManager()
        
        session = manager.create_session("game_001", "client_abc")
        registration = manager.register_npc("npc_001", session.session_id)
        
        data = registration.to_dict()
        
        assert data["npc_id"] == "npc_001"
        assert data["session_id"] == session.session_id


class TestGetSessionNPCs:
    """Tests for getting session NPCs."""

    def test_get_session_npcs(self):
        """Test getting NPCs in a session."""
        manager = SessionManager()
        
        session = manager.create_session("game_001", "client_abc")
        manager.register_npc("npc_001", session.session_id)
        manager.register_npc("npc_002", session.session_id)
        
        npcs = manager.get_session_npcs(session.session_id)
        
        assert len(npcs) == 2
        assert "npc_001" in npcs
        assert "npc_002" in npcs

    def test_get_session_npcs_empty(self):
        """Test getting NPCs for empty session."""
        manager = SessionManager()
        
        session = manager.create_session("game_001", "client_abc")
        
        npcs = manager.get_session_npcs(session.session_id)
        
        assert len(npcs) == 0

    def test_get_session_npcs_nonexistent(self):
        """Test getting NPCs for nonexistent session."""
        manager = SessionManager()
        
        npcs = manager.get_session_npcs("nonexistent_session")
        
        assert len(npcs) == 0


class TestGlobalSessionManager:
    """Tests for global session manager."""

    def test_get_session_manager(self):
        """Test getting global session manager."""
        manager = get_session_manager()
        
        assert manager is not None
        assert isinstance(manager, SessionManager)

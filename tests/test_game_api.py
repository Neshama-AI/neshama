"""
Neshama Game API Tests
"""

import pytest
import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.web.server import create_app
from neshama.soul.npc_manager import create_npc_manager, NPCManager


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def clean_manager():
    """Create a clean NPC manager for testing."""
    manager = create_npc_manager()
    # Clear any existing NPCs
    for npc in manager.list_npcs():
        manager.delete_npc(npc.npc_id)
    return manager


class TestGameEventEndpoints:
    """Tests for game event endpoints."""

    def test_list_events(self, client):
        """Test listing all game events."""
        response = client.get("/api/game/events")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["count"] == 15
        assert len(data["data"]["events"]) == 15

    def test_get_event_info(self, client):
        """Test getting info about a specific event."""
        response = client.get("/api/game/events/quest_completed")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["event_type"] == "quest_completed"
        assert "joy" in data["data"]["affected_emotions"]

    def test_invalid_event_type(self, client, clean_manager):
        """Test error on invalid event type."""
        # Create NPC first
        create_response = client.post(
            "/api/game/npc",
            params={"name": "Event Test NPC"}
        )
        npc_id = create_response.json()["data"]["npc_id"]
        
        response = client.post(
            f"/api/game/npc/{npc_id}/event",
            params={"event_type": "invalid_event", "intensity": 0.5}
        )
        
        assert response.status_code == 400

    def test_push_event_to_nonexistent_npc(self, client, clean_manager):
        """Test error when pushing event to non-existent NPC."""
        response = client.post(
            "/api/game/npc/nonexistent-id/event",
            params={"event_type": "player_helped", "intensity": 0.5}
        )
        
        assert response.status_code == 404


class TestEmotionEndpoints:
    """Tests for emotion state endpoints."""

    def test_create_npc_and_get_emotion(self, client, clean_manager):
        """Test creating NPC and getting emotion state."""
        # Create NPC
        create_response = client.post(
            "/api/game/npc",
            params={"name": "Test NPC"}
        )
        assert create_response.status_code == 200
        npc_id = create_response.json()["data"]["npc_id"]
        
        # Get emotion state
        response = client.get(f"/api/game/npc/{npc_id}/emotion")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "emotion_state" in data["data"]

    def test_clear_emotions(self, client, clean_manager):
        """Test clearing NPC emotions."""
        # Create NPC
        create_response = client.post(
            "/api/game/npc",
            params={"name": "Test NPC"}
        )
        npc_id = create_response.json()["data"]["npc_id"]
        
        # Clear emotions
        response = client.post(f"/api/game/npc/{npc_id}/emotion/clear")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["cleared"] is True

    def test_tick_emotions(self, client, clean_manager):
        """Test ticking emotions (decay)."""
        # Create NPC
        create_response = client.post(
            "/api/game/npc",
            params={"name": "Test NPC"}
        )
        npc_id = create_response.json()["data"]["npc_id"]
        
        # Tick
        response = client.post(
            f"/api/game/npc/{npc_id}/emotion/tick",
            params={"delta_seconds": 60.0}
        )
        
        assert response.status_code == 200


class TestBehaviorEndpoints:
    """Tests for behavior endpoints."""

    def test_get_behavior(self, client, clean_manager):
        """Test getting behavior profile."""
        # Create NPC
        create_response = client.post(
            "/api/game/npc",
            params={"name": "Test NPC"}
        )
        npc_id = create_response.json()["data"]["npc_id"]
        
        # Get behavior
        response = client.get(f"/api/game/npc/{npc_id}/behavior")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "dialogue_style" in data["data"]
        assert "movement_pattern" in data["data"]


class TestNPCCRUD:
    """Tests for NPC CRUD operations."""

    def test_create_npc(self, client, clean_manager):
        """Test creating a new NPC."""
        response = client.post(
            "/api/game/npc",
            params={"name": "Test Tavern Keeper"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Test Tavern Keeper"
        assert "npc_id" in data["data"]
        assert "personality" in data["data"]

    def test_create_npc_with_preset(self, client, clean_manager):
        """Test creating NPC with preset."""
        response = client.post(
            "/api/game/npc",
            params={"name": "Tavern Owner", "preset": "tavern_keeper"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["personality"]["extraversion"] == 0.8

    def test_create_npc_with_custom_personality(self, client, clean_manager):
        """Test creating NPC with custom personality."""
        personality = {
            "openness": 0.9,
            "extraversion": 0.9,
        }
        response = client.post(
            "/api/game/npc",
            params={"name": "Custom NPC"},
            json=personality
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["personality"]["openness"] == 0.9

    def test_get_profile(self, client, clean_manager):
        """Test getting NPC profile."""
        # Create NPC
        create_response = client.post(
            "/api/game/npc",
            params={"name": "Profile Test NPC"}
        )
        npc_id = create_response.json()["data"]["npc_id"]
        
        # Get profile
        response = client.get(f"/api/game/npc/{npc_id}/profile")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "Profile Test NPC"
        assert "personality" in data["data"]

    def test_list_npcs(self, client, clean_manager):
        """Test listing all NPCs."""
        # Create some NPCs
        client.post("/api/game/npc", params={"name": "NPC 1"})
        client.post("/api/game/npc", params={"name": "NPC 2"})
        
        response = client.get("/api/game/npc")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["count"] >= 2

    def test_delete_npc(self, client, clean_manager):
        """Test deleting an NPC."""
        # Create NPC
        create_response = client.post(
            "/api/game/npc",
            params={"name": "To Delete"}
        )
        npc_id = create_response.json()["data"]["npc_id"]
        
        # Delete
        response = client.delete(f"/api/game/npc/{npc_id}")
        
        assert response.status_code == 200
        assert response.json()["data"]["deleted"] is True
        
        # Verify deleted
        get_response = client.get(f"/api/game/npc/{npc_id}/profile")
        assert get_response.status_code == 404

    def test_get_nonexistent_npc(self, client, clean_manager):
        """Test error on non-existent NPC."""
        response = client.get("/api/game/npc/nonexistent-id/profile")
        assert response.status_code == 404


class TestMemoryEndpoints:
    """Tests for memory and relations endpoints."""

    def test_get_memory(self, client, clean_manager):
        """Test getting NPC memory."""
        # Create NPC
        create_response = client.post(
            "/api/game/npc",
            params={"name": "Memory Test NPC"}
        )
        npc_id = create_response.json()["data"]["npc_id"]
        
        response = client.get(f"/api/game/npc/{npc_id}/memory")
        
        assert response.status_code == 200
        data = response.json()
        assert "relations" in data["data"]

    def test_remember_entity(self, client, clean_manager):
        """Test making NPC remember an entity."""
        # Create NPC
        create_response = client.post(
            "/api/game/npc",
            params={"name": "Remember Test NPC"}
        )
        npc_id = create_response.json()["data"]["npc_id"]
        
        response = client.post(
            f"/api/game/npc/{npc_id}/remember",
            params={
                "entity_id": "player_001",
                "relation_type": "friend",
                "weight": 0.8
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["weight"] == 0.8

    def test_get_relations(self, client, clean_manager):
        """Test getting NPC relations."""
        # Create NPC
        create_response = client.post(
            "/api/game/npc",
            params={"name": "Relations Test NPC"}
        )
        npc_id = create_response.json()["data"]["npc_id"]
        
        # Add relation
        client.post(
            f"/api/game/npc/{npc_id}/remember",
            params={
                "entity_id": "player_001",
                "relation_type": "friend",
                "weight": 0.8
            }
        )
        
        response = client.get(f"/api/game/npc/{npc_id}/relations")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["relations"]) > 0


class TestPresetEndpoints:
    """Tests for preset endpoints."""

    def test_list_presets(self, client, clean_manager):
        """Test listing available presets."""
        response = client.get("/api/game/presets")
        
        assert response.status_code == 200
        data = response.json()
        assert "presets" in data["data"]
        assert "tavern_keeper" in data["data"]["presets"]
        assert "guard_captain" in data["data"]["presets"]

    def test_get_preset_info(self, client, clean_manager):
        """Test getting preset information."""
        response = client.get("/api/game/presets/tavern_keeper")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "tavern_keeper"
        assert "personality" in data["data"]
        assert data["data"]["personality"]["extraversion"] == 0.8

    def test_get_nonexistent_preset(self, client, clean_manager):
        """Test error on non-existent preset."""
        response = client.get("/api/game/presets/nonexistent")
        assert response.status_code == 404


class TestChatEndpoint:
    """Tests for chat endpoint."""

    def test_chat_with_npc(self, client, clean_manager):
        """Test chatting with NPC."""
        # Create NPC
        create_response = client.post(
            "/api/game/npc",
            params={"name": "Chat Test NPC"}
        )
        npc_id = create_response.json()["data"]["npc_id"]
        
        response = client.post(
            f"/api/game/npc/{npc_id}/chat",
            params={"message": "Hello!"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "system_context" in data["data"]
        assert "emotion_context" in data["data"]
        assert data["data"]["npc_name"] == "Chat Test NPC"

    def test_chat_returns_context_for_llm(self, client, clean_manager):
        """Test that chat returns proper context for LLM injection."""
        # Create NPC
        create_response = client.post(
            "/api/game/npc",
            params={"name": "LLM Context Test"}
        )
        npc_id = create_response.json()["data"]["npc_id"]
        
        response = client.post(
            f"/api/game/npc/{npc_id}/chat",
            params={"message": "Tell me about yourself"}
        )
        
        assert response.status_code == 200
        data = response.json()
        context = data["data"]["system_context"]
        
        assert "npc_name" in context
        assert "personality" in context
        assert "emotion_state" in context
        assert "behavior" in context


class TestEventProcessing:
    """Tests for full event processing flow."""

    def test_full_event_to_behavior_flow(self, client, clean_manager):
        """Test complete flow: event → emotion → behavior."""
        # Create NPC
        create_response = client.post(
            "/api/game/npc",
            params={"name": "Flow Test NPC", "preset": "tavern_keeper"}
        )
        npc_id = create_response.json()["data"]["npc_id"]
        
        # Push event (player helped NPC)
        event_response = client.post(
            f"/api/game/npc/{npc_id}/event",
            params={"event_type": "player_helped", "intensity": 0.8}
        )
        assert event_response.status_code == 200
        
        # Get emotion state
        emotion_response = client.get(f"/api/game/npc/{npc_id}/emotion")
        assert emotion_response.status_code == 200
        emotions = emotion_response.json()["data"]["emotion_state"]
        assert "trust" in emotions
        assert emotions["trust"] > 0
        
        # Get behavior
        behavior_response = client.get(f"/api/game/npc/{npc_id}/behavior")
        assert behavior_response.status_code == 200
        behavior = behavior_response.json()["data"]
        # After BUG fix, single player_helped gives trust=0.4, joy=0.3
        # which may not be enough for "friendly" dialogue style (threshold 0.5)
        assert behavior["dialogue_style"] in ["friendly", "excited", "neutral"]

    def test_anger_flow(self, client, clean_manager):
        """Test anger flow: insult → anger → hostile."""
        # Create NPC
        create_response = client.post(
            "/api/game/npc",
            params={"name": "Anger Test NPC"}
        )
        npc_id = create_response.json()["data"]["npc_id"]
        
        # Insult NPC multiple times to build up anger
        for _ in range(3):
            client.post(
                f"/api/game/npc/{npc_id}/event",
                params={"event_type": "npc_insulted", "intensity": 1.0}
            )
        
        # Get behavior
        behavior_response = client.get(f"/api/game/npc/{npc_id}/behavior")
        behavior = behavior_response.json()["data"]
        
        # Should be hostile or aggressive
        assert behavior["dialogue_style"] in ["hostile", "aggressive"]

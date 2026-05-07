"""
Neshama Social API Tests
"""

import pytest
import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.web.server import create_app
from neshama.soul.npc_manager import create_npc_manager


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


@pytest.fixture
def setup_npcs(client, clean_manager):
    """Set up test NPCs."""
    npcs = {}
    
    # Create test NPCs
    for name in ["Alice", "Bob", "Charlie"]:
        response = client.post(
            "/api/game/npc",
            params={"name": name}
        )
        assert response.status_code == 200
        npcs[name] = response.json()["data"]["npc_id"]
    
    return npcs


class TestNPCInteractionEndpoint:
    """Tests for NPC interaction API."""
    
    def test_trigger_interaction(self, client, setup_npcs):
        """Test triggering NPC interaction."""
        alice_id = setup_npcs["Alice"]
        bob_id = setup_npcs["Bob"]
        
        response = client.post(
            f"/api/game/npc/{alice_id}/interact/{bob_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "event" in data["data"]
        assert "relationship" in data["data"]
    
    def test_trigger_interaction_with_type(self, client, setup_npcs):
        """Test triggering specific interaction type."""
        alice_id = setup_npcs["Alice"]
        bob_id = setup_npcs["Bob"]
        
        response = client.post(
            f"/api/game/npc/{alice_id}/interact/{bob_id}",
            params={"interaction_type": "gossip"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_trigger_interaction_invalid_type(self, client, setup_npcs):
        """Test error on invalid interaction type."""
        alice_id = setup_npcs["Alice"]
        bob_id = setup_npcs["Bob"]
        
        response = client.post(
            f"/api/game/npc/{alice_id}/interact/{bob_id}",
            params={"interaction_type": "invalid_type"}
        )
        
        assert response.status_code == 400
    
    def test_trigger_interaction_nonexistent_npc(self, client, setup_npcs):
        """Test error on nonexistent NPC."""
        alice_id = setup_npcs["Alice"]
        
        response = client.post(
            f"/api/game/npc/{alice_id}/interact/nonexistent_id"
        )
        
        assert response.status_code == 404


class TestSocialGraphEndpoint:
    """Tests for social graph API."""
    
    def test_get_social_graph(self, client, setup_npcs):
        """Test getting social graph."""
        alice_id = setup_npcs["Alice"]
        
        response = client.get(f"/api/game/npc/{alice_id}/social-graph")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "friends" in data["data"]
        assert "enemies" in data["data"]
        assert "neutrals" in data["data"]


class TestMutualRelationEndpoint:
    """Tests for mutual relation API."""
    
    def test_get_mutual_relation(self, client, setup_npcs):
        """Test getting mutual relation."""
        alice_id = setup_npcs["Alice"]
        bob_id = setup_npcs["Bob"]
        
        # First create a relation
        client.post(f"/api/game/npc/{alice_id}/interact/{bob_id}")
        
        response = client.get(
            f"/api/game/npc/{alice_id}/relations/{bob_id}/mutual"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "relation" in data["data"]
        assert "can_interact" in data["data"]
        assert "suggested_interaction" in data["data"]
    
    def test_get_mutual_relation_nonexistent(self, client, setup_npcs):
        """Test error on nonexistent NPC."""
        alice_id = setup_npcs["Alice"]
        
        response = client.get(
            f"/api/game/npc/{alice_id}/relations/nonexistent/mutual"
        )
        
        assert response.status_code == 404


class TestNPCKnowledgeEndpoint:
    """Tests for NPC knowledge API."""
    
    def test_get_knowledge(self, client, setup_npcs):
        """Test getting NPC knowledge."""
        alice_id = setup_npcs["Alice"]
        
        response = client.get(f"/api/game/npc/{alice_id}/knowledge")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "known_info" in data["data"]
    
    def test_get_knowledge_with_filter(self, client, setup_npcs):
        """Test getting knowledge with type filter."""
        alice_id = setup_npcs["Alice"]
        
        response = client.get(
            f"/api/game/npc/{alice_id}/knowledge",
            params={"info_type": "world_event"}
        )
        
        assert response.status_code == 200
    
    def test_get_knowledge_nonexistent_npc(self, client, clean_manager):
        """Test error on nonexistent NPC."""
        response = client.get("/api/game/npc/nonexistent_id/knowledge")
        
        assert response.status_code == 404


class TestSpreadInformationEndpoint:
    """Tests for information spread API."""
    
    def test_spread_information(self, client, setup_npcs):
        """Test spreading information."""
        alice_id = setup_npcs["Alice"]
        bob_id = setup_npcs["Bob"]
        charlie_id = setup_npcs["Charlie"]
        
        response = client.post(
            f"/api/game/npc/{alice_id}/spread-info",
            json={
                "info_type": "world_event",
                "content": "A dragon appeared!",
                "targets": [bob_id, charlie_id],
                "importance": 0.8,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "spread_to" in data["data"]
    
    def test_spread_information_invalid_type(self, client, setup_npcs):
        """Test error on invalid info type."""
        alice_id = setup_npcs["Alice"]
        bob_id = setup_npcs["Bob"]
        
        response = client.post(
            f"/api/game/npc/{alice_id}/spread-info",
            json={
                "info_type": "invalid_type",
                "content": "Test",
                "targets": [bob_id],
            }
        )
        
        assert response.status_code == 400
    
    def test_spread_information_invalid_target(self, client, setup_npcs):
        """Test error on invalid target."""
        alice_id = setup_npcs["Alice"]
        
        response = client.post(
            f"/api/game/npc/{alice_id}/spread-info",
            json={
                "info_type": "world_event",
                "content": "Test",
                "targets": ["nonexistent_id"],
            }
        )
        
        assert response.status_code == 404


class TestInformationDetailsEndpoint:
    """Tests for information details API."""
    
    def test_get_information_details(self, client, setup_npcs):
        """Test getting information details."""
        alice_id = setup_npcs["Alice"]
        bob_id = setup_npcs["Bob"]
        
        # First spread some info
        spread_response = client.post(
            f"/api/game/npc/{alice_id}/spread-info",
            json={
                "info_type": "quest_info",
                "content": "Help needed!",
                "targets": [bob_id],
            }
        )
        
        info_id = spread_response.json()["data"]["info_id"]
        
        # Get details
        response = client.get(f"/api/game/information/{info_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "chain" in data["data"]
    
    def test_get_information_not_found(self, client, clean_manager):
        """Test error on nonexistent info."""
        response = client.get("/api/game/information/nonexistent_id")
        
        assert response.status_code == 404


class TestNPCDialogueEndpoint:
    """Tests for NPC dialogue API."""
    
    def test_generate_dialogue(self, client, setup_npcs):
        """Test generating NPC dialogue."""
        alice_id = setup_npcs["Alice"]
        bob_id = setup_npcs["Bob"]
        
        response = client.post(
            f"/api/game/npc/{alice_id}/dialogue/{bob_id}",
            params={
                "topic": "The weather",
                "trigger": "player_triggered",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "dialogue_id" in data["data"]
        assert "turns" in data["data"]
    
    def test_generate_dialogue_nonexistent(self, client, setup_npcs):
        """Test error on nonexistent NPC."""
        alice_id = setup_npcs["Alice"]
        
        response = client.post(
            f"/api/game/npc/{alice_id}/dialogue/nonexistent",
            params={"topic": "Test"}
        )
        
        assert response.status_code == 404
    
    def test_continue_dialogue(self, client, setup_npcs):
        """Test continuing dialogue."""
        alice_id = setup_npcs["Alice"]
        bob_id = setup_npcs["Bob"]
        
        # First create dialogue
        create_response = client.post(
            f"/api/game/npc/{alice_id}/dialogue/{bob_id}",
            params={"topic": "Test"}
        )
        
        dialogue_id = create_response.json()["data"]["dialogue_id"]
        
        # Continue
        response = client.post(
            f"/api/game/dialogue/{dialogue_id}/continue"
        )
        
        assert response.status_code == 200
    
    def test_continue_dialogue_not_found(self, client, clean_manager):
        """Test error on nonexistent dialogue."""
        response = client.post(
            "/api/game/dialogue/nonexistent/continue"
        )
        
        assert response.status_code == 404
    
    def test_summarize_dialogue(self, client, setup_npcs):
        """Test summarizing dialogue."""
        alice_id = setup_npcs["Alice"]
        bob_id = setup_npcs["Bob"]
        
        # First create dialogue
        create_response = client.post(
            f"/api/game/npc/{alice_id}/dialogue/{bob_id}",
            params={"topic": "Test"}
        )
        
        dialogue_id = create_response.json()["data"]["dialogue_id"]
        
        # Summarize
        response = client.post(
            f"/api/game/dialogue/{dialogue_id}/summarize"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data["data"]


class TestSocialEventsEndpoint:
    """Tests for social events API."""
    
    def test_get_social_events(self, client, setup_npcs):
        """Test getting social events."""
        alice_id = setup_npcs["Alice"]
        bob_id = setup_npcs["Bob"]
        
        # Create some interactions
        client.post(f"/api/game/npc/{alice_id}/interact/{bob_id}")
        
        response = client.get("/api/game/social/events")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "events" in data["data"]
    
    def test_get_social_events_filtered(self, client, setup_npcs):
        """Test getting events filtered by NPC."""
        alice_id = setup_npcs["Alice"]
        bob_id = setup_npcs["Bob"]
        
        client.post(f"/api/game/npc/{alice_id}/interact/{bob_id}")
        
        response = client.get(
            "/api/game/social/events",
            params={"npc_id": alice_id}
        )
        
        assert response.status_code == 200


class TestSocialTickEndpoint:
    """Tests for social tick API."""
    
    def test_social_tick(self, client, clean_manager):
        """Test triggering social tick."""
        response = client.post("/api/game/social/tick")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "events" in data["data"]
    
    def test_social_tick_with_session(self, client, setup_npcs, clean_manager):
        """Test tick with session filter."""
        response = client.post(
            "/api/game/social/tick",
            params={"session_id": "test_session"}
        )
        
        assert response.status_code == 200


class TestInformationDecayEndpoint:
    """Tests for information decay API."""
    
    def test_decay_information(self, client, clean_manager):
        """Test information decay."""
        response = client.post(
            "/api/game/information/decay",
            params={"delta_seconds": 60.0}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "decayed_count" in data["data"]


class TestSocialStatsEndpoint:
    """Tests for social stats API."""
    
    def test_get_social_stats(self, client, clean_manager):
        """Test getting social stats."""
        response = client.get("/api/game/social/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "relations_count" in data["data"]
        assert "information_count" in data["data"]

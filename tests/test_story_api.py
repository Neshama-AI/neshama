"""
Neshama Story API Tests
"""

import pytest
import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.web.server import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestStoryTriggerEndpoints:
    """Tests for story trigger API endpoints."""

    def test_list_triggers_empty(self, client):
        """Test listing triggers when none registered."""
        response = client.get("/api/game/story/triggers")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "triggers" in data["data"]

    def test_register_trigger(self, client):
        """Test registering a story trigger."""
        response = client.post(
            "/api/game/story/trigger",
            params={
                "trigger_id": "test_register_trigger",
                "name": "测试注册",
                "description": "测试描述",
                "cooldown": 60.0,
                "priority": 10,
                "one_shot": False,
            },
            json={
                "conditions": [
                    {
                        "condition_type": "emotion_threshold",
                        "npc_id": "npc_001",
                        "emotion": "anger",
                        "threshold": 0.8,
                        "direction": "rising",
                    }
                ],
                "effects": [
                    {
                        "effect_type": "trigger_world_event",
                        "target": "test_event",
                        "params": {},
                    }
                ],
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["trigger_id"] == "test_register_trigger"

    def test_activate_trigger(self, client):
        """Test manually activating a trigger."""
        # First register a trigger
        client.post(
            "/api/game/story/trigger",
            params={
                "trigger_id": "test_activate",
                "name": "测试激活",
                "description": "测试描述",
            },
            json={
                "conditions": [
                    {
                        "condition_type": "emotion_threshold",
                        "npc_id": "npc_001",
                        "emotion": "anger",
                        "threshold": 0.5,
                        "direction": "rising",
                    }
                ],
                "effects": [{"effect_type": "send_notification", "target": "test"}],
            },
        )
        
        # Then activate it
        response = client.post(
            "/api/game/story/trigger/test_activate/activate",
            json={
                "npc_emotions": {"npc_001": {"anger": 0.8}}
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["triggered"] is True

    def test_get_active_story_events(self, client):
        """Test getting active story events."""
        response = client.get("/api/game/story/active")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "events" in data["data"]

    def test_check_all_triggers(self, client):
        """Test checking all triggers."""
        response = client.post(
            "/api/game/story/check",
            json={
                "npc_emotions": {
                    "npc_001": {"anger": 0.8, "joy": 0.3}
                }
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "events" in data["data"]


class TestQuestEndpoints:
    """Tests for quest API endpoints."""

    def test_list_quest_templates(self, client):
        """Test listing quest templates."""
        response = client.get("/api/game/quest/templates")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["count"] >= 5  # Default templates

    def test_get_available_quests_empty(self, client):
        """Test getting available quests (none generated)."""
        response = client.get("/api/game/quest/available")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_generate_quest(self, client):
        """Test generating a quest from template."""
        response = client.post(
            "/api/game/quest/generate",
            params={
                "template_id": "sad_quest",
                "npc_id": "tavern_keeper",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["template_id"] == "sad_quest"
        assert data["data"]["status"] == "available"

    def test_generate_quest_with_custom_title(self, client):
        """Test generating quest with custom title."""
        response = client.post(
            "/api/game/quest/generate",
            params={
                "template_id": "sad_quest",
                "npc_id": "npc_001",
                "title": "帮我找东西",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["title"] == "帮我找东西"

    def test_get_quest(self, client):
        """Test getting quest details."""
        # Generate quest first
        gen_response = client.post(
            "/api/game/quest/generate",
            params={
                "template_id": "sad_quest",
                "npc_id": "npc_001",
            },
        )
        assert gen_response.status_code == 200
        quest_id = gen_response.json()["data"]["quest_id"]
        
        # Get quest
        response = client.get(f"/api/game/quest/{quest_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["quest_id"] == quest_id

    def test_accept_quest(self, client):
        """Test accepting a quest."""
        # Generate quest
        gen_response = client.post(
            "/api/game/quest/generate",
            params={
                "template_id": "sad_quest",
                "npc_id": "npc_001",
            },
        )
        quest_id = gen_response.json()["data"]["quest_id"]
        
        # Accept quest
        response = client.post(f"/api/game/quest/{quest_id}/accept")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "active"
        assert data["data"]["accepted_at"] is not None

    def test_update_quest_progress(self, client):
        """Test updating quest progress."""
        # Generate and accept quest
        gen_response = client.post(
            "/api/game/quest/generate",
            params={
                "template_id": "friend_favor",  # Use different template
                "npc_id": "npc_002",  # Use different NPC
            },
        )
        assert gen_response.status_code == 200
        quest_id = gen_response.json()["data"]["quest_id"]
        client.post(f"/api/game/quest/{quest_id}/accept")
        
        # Update progress
        response = client.post(
            f"/api/game/quest/{quest_id}/progress",
            params={
                "event_type": "item_collected",
                "event_target": "lost_item",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_complete_quest(self, client):
        """Test completing a quest."""
        # Generate and accept quest
        gen_response = client.post(
            "/api/game/quest/generate",
            params={
                "template_id": "angry_lockdown",  # Use different template
                "npc_id": "npc_003",  # Use different NPC
            },
        )
        assert gen_response.status_code == 200
        quest_id = gen_response.json()["data"]["quest_id"]
        client.post(f"/api/game/quest/{quest_id}/accept")
        
        # Complete quest
        response = client.post(f"/api/game/quest/{quest_id}/complete")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "completed"
        assert data["data"]["completed_at"] is not None

    def test_fail_quest(self, client):
        """Test failing a quest."""
        # Generate and accept quest
        gen_response = client.post(
            "/api/game/quest/generate",
            params={
                "template_id": "betrayal_revenge",  # Use different template
                "npc_id": "npc_004",  # Use different NPC
            },
        )
        assert gen_response.status_code == 200
        quest_id = gen_response.json()["data"]["quest_id"]
        client.post(f"/api/game/quest/{quest_id}/accept")
        
        # Fail quest
        response = client.post(f"/api/game/quest/{quest_id}/fail")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "failed"
        assert data["data"]["failed_at"] is not None

    def test_check_quest_triggers(self, client):
        """Test checking quest triggers for NPC."""
        response = client.post(
            "/api/game/quest/check-triggers",
            params={
                "npc_id": "npc_001",
                "emotion_state": {"anger": 0.8, "joy": 0.2},
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["npc_id"] == "npc_001"

    def test_get_active_quests(self, client):
        """Test getting active quests."""
        response = client.get("/api/game/quest/active")
        
        assert response.status_code == 200
        data = response.json()
        assert "quests" in data["data"]


class TestWorldEventEndpoints:
    """Tests for world event API endpoints."""

    def test_get_world_events_empty(self, client):
        """Test getting world events when none exist."""
        response = client.get("/api/game/world/events")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["count"] == 0

    def test_emit_world_event(self, client):
        """Test emitting a world event."""
        response = client.post(
            "/api/game/world/events",
            params={
                "event_type": "area_lockdown",
                "source_npc_id": "tavern_keeper",
                "title": "酒馆封锁",
            },
            json={
                "params": {
                    "area_id": "tavern_main",
                    "area_name": "酒馆大厅",
                }
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["event_type"] == "area_lockdown"

    def test_get_world_event(self, client):
        """Test getting a specific world event."""
        # Emit event first
        emit_response = client.post(
            "/api/game/world/events",
            params={
                "event_type": "price_change",
                "source_npc_id": "merchant",
            },
            json={"params": {"shop_id": "store_1"}},
        )
        event_id = emit_response.json()["data"]["event_id"]
        
        # Get event
        response = client.get(f"/api/game/world/events/{event_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["event_id"] == event_id

    def test_resolve_world_event(self, client):
        """Test resolving a world event."""
        # Emit event
        emit_response = client.post(
            "/api/game/world/events",
            params={
                "event_type": "area_lockdown",
                "source_npc_id": "npc1",
            },
            json={"params": {}},
        )
        event_id = emit_response.json()["data"]["event_id"]
        
        # Resolve event
        response = client.post(
            f"/api/game/world/events/{event_id}/resolve",
            params={
                "resolution": "player_action",
            },
            json={"params": {"method": "persuasion"}},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["resolved"] is True

    def test_get_world_events_by_type(self, client):
        """Test filtering world events by type."""
        # Emit multiple event types
        client.post(
            "/api/game/world/events",
            params={"event_type": "area_lockdown", "source_npc_id": "npc1"},
            json={"params": {}},
        )
        client.post(
            "/api/game/world/events",
            params={"event_type": "price_change", "source_npc_id": "npc2"},
            json={"params": {}},
        )
        
        # Filter by type
        response = client.get(
            "/api/game/world/events",
            params={"event_type": "area_lockdown"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(e["event_type"] == "area_lockdown" for e in data["data"]["events"])

    def test_invalid_event_type(self, client):
        """Test error on invalid event type."""
        response = client.post(
            "/api/game/world/events",
            params={
                "event_type": "invalid_type",
                "source_npc_id": "npc1",
            },
            json={"params": {}},
        )
        
        assert response.status_code == 400

    def test_get_event_history(self, client):
        """Test getting event history."""
        # Emit and resolve an event
        emit_response = client.post(
            "/api/game/world/events",
            params={"event_type": "area_lockdown", "source_npc_id": "npc1"},
            json={"params": {}},
        )
        event_id = emit_response.json()["data"]["event_id"]
        client.post(
            f"/api/game/world/events/{event_id}/resolve",
            params={"resolution": "manual"},
        )
        
        # Get history
        response = client.get(f"/api/game/world/events/{event_id}/history")
        
        assert response.status_code == 200
        data = response.json()
        assert "history" in data["data"]

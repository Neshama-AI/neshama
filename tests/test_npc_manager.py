"""
Neshama NPC Manager Tests
"""

import pytest
import sys
import os
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.soul.npc_manager import (
    NPCManager,
    NPCSoul,
    PersonalityProfile,
    create_npc_manager,
)
from neshama.soul.emotion.game_event import GameEvent, GameEventType


@pytest.fixture
def temp_npc_dir():
    """Create a temporary directory for NPC data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def manager(temp_npc_dir):
    """Create a manager with temp directory."""
    # Copy presets to temp directory
    import shutil
    presets_src = Path(__file__).parent.parent / "npc_data" / "presets"
    if presets_src.exists():
        presets_dest = temp_npc_dir / "presets"
        shutil.copytree(presets_src, presets_dest)
    
    return NPCManager(npc_dir=temp_npc_dir)


class TestPersonalityProfile:
    """Tests for PersonalityProfile dataclass."""

    def test_default_profile(self):
        """Test default profile values."""
        profile = PersonalityProfile()
        
        assert profile.openness == 0.5
        assert profile.conscientiousness == 0.5
        assert profile.extraversion == 0.5
        assert profile.agreeableness == 0.5
        assert profile.neuroticism == 0.5

    def test_custom_profile(self):
        """Test custom profile values."""
        profile = PersonalityProfile(
            openness=0.8,
            extraversion=0.9,
        )
        
        assert profile.openness == 0.8
        assert profile.extraversion == 0.9

    def test_to_dict(self):
        """Test serialization to dict."""
        profile = PersonalityProfile(openness=0.7)
        d = profile.to_dict()
        
        assert d["openness"] == 0.7
        assert "extraversion" in d

    def test_from_dict(self):
        """Test creation from dict."""
        data = {"openness": 0.8, "extraversion": 0.6}
        profile = PersonalityProfile.from_dict(data)
        
        assert profile.openness == 0.8
        assert profile.extraversion == 0.6


class TestNPCSoul:
    """Tests for NPCSoul dataclass."""

    def test_create_soul(self):
        """Test basic soul creation."""
        soul = NPCSoul(
            npc_id="test-001",
            name="Test NPC",
            personality=PersonalityProfile(),
        )
        
        assert soul.npc_id == "test-001"
        assert soul.name == "Test NPC"
        assert isinstance(soul.personality, PersonalityProfile)

    def test_to_dict(self):
        """Test serialization."""
        soul = NPCSoul(
            npc_id="test-001",
            name="Test NPC",
            personality=PersonalityProfile(),
        )
        d = soul.to_dict()
        
        assert d["npc_id"] == "test-001"
        assert d["name"] == "Test NPC"
        assert "personality" in d

    def test_from_dict(self):
        """Test creation from dict."""
        data = {
            "npc_id": "test-001",
            "name": "Test NPC",
            "personality": {"openness": 0.7},
        }
        soul = NPCSoul.from_dict(data)
        
        assert soul.npc_id == "test-001"
        assert soul.personality.openness == 0.7


class TestNPCManagerInit:
    """Tests for NPCManager initialization."""

    def test_create_manager(self, temp_npc_dir):
        """Test manager creation."""
        manager = NPCManager(npc_dir=temp_npc_dir)
        
        assert manager._npc_dir == temp_npc_dir
        assert isinstance(manager._souls, dict)

    def test_manager_creates_directory(self, temp_npc_dir):
        """Test that manager creates NPC directory."""
        NPCManager(npc_dir=temp_npc_dir)
        
        assert temp_npc_dir.exists()


class TestNPCCreate:
    """Tests for NPC creation."""

    def test_create_npc(self, manager):
        """Test creating a new NPC."""
        soul = manager.create_npc(name="Test NPC")
        
        assert soul.name == "Test NPC"
        assert soul.npc_id is not None
        assert len(soul.npc_id) == 36  # UUID format

    def test_create_npc_with_custom_id(self, manager):
        """Test creating NPC with custom ID."""
        soul = manager.create_npc(name="Custom ID NPC", npc_id="custom-123")
        
        assert soul.npc_id == "custom-123"

    def test_create_npc_with_personality(self, manager):
        """Test creating NPC with custom personality."""
        personality = {"openness": 0.9, "extraversion": 0.8}
        soul = manager.create_npc(
            name="Personality NPC",
            personality=personality,
        )
        
        assert soul.personality.openness == 0.9
        assert soul.personality.extraversion == 0.8

    def test_create_npc_with_preset(self, manager):
        """Test creating NPC from preset."""
        soul = manager.create_npc(
            name="Tavern Owner",
            preset="tavern_keeper",
        )
        
        assert soul.personality.extraversion == 0.8
        assert soul.personality.agreeableness == 0.75

    def test_create_npc_guard_captain(self, manager):
        """Test creating NPC from guard_captain preset."""
        soul = manager.create_npc(
            name="Guard Captain",
            preset="guard_captain",
        )
        
        assert soul.personality.conscientiousness == 0.9
        assert soul.personality.neuroticism == 0.2

    def test_create_duplicate_id_fails(self, manager):
        """Test that creating NPC with duplicate ID fails."""
        manager.create_npc(name="NPC 1", npc_id="same-id")
        
        with pytest.raises(ValueError):
            manager.create_npc(name="NPC 2", npc_id="same-id")


class TestNPCGet:
    """Tests for NPC retrieval."""

    def test_get_existing_npc(self, manager):
        """Test getting existing NPC."""
        created = manager.create_npc(name="Get Test")
        
        retrieved = manager.get_npc(created.npc_id)
        
        assert retrieved is not None
        assert retrieved.npc_id == created.npc_id
        assert retrieved.name == "Get Test"

    def test_get_nonexistent_npc(self, manager):
        """Test getting non-existent NPC returns None."""
        result = manager.get_npc("nonexistent")
        
        assert result is None

    def test_list_npcs(self, manager):
        """Test listing NPCs."""
        manager.create_npc(name="NPC 1")
        manager.create_npc(name="NPC 2")
        manager.create_npc(name="NPC 3")
        
        npcs = manager.list_npcs()
        
        assert len(npcs) == 3
        assert all(isinstance(npc, NPCSoul) for npc in npcs)


class TestNPCDelete:
    """Tests for NPC deletion."""

    def test_delete_npc(self, manager):
        """Test deleting an NPC."""
        soul = manager.create_npc(name="To Delete")
        
        result = manager.delete_npc(soul.npc_id)
        
        assert result is True
        assert manager.get_npc(soul.npc_id) is None

    def test_delete_nonexistent(self, manager):
        """Test deleting non-existent NPC."""
        result = manager.delete_npc("nonexistent")
        
        assert result is False

    def test_delete_removes_file(self, manager, temp_npc_dir):
        """Test that delete removes the file."""
        soul = manager.create_npc(name="File Test")
        file_path = manager._get_file_path(soul.npc_id)
        
        assert file_path.exists()
        
        manager.delete_npc(soul.npc_id)
        
        assert not file_path.exists()


class TestProcessEvent:
    """Tests for event processing."""

    def test_process_event(self, manager):
        """Test processing a game event."""
        soul = manager.create_npc(name="Event Test")
        
        event = GameEvent(GameEventType.PLAYER_HELPED, intensity=0.8)
        result = manager.process_event(soul.npc_id, event)
        
        assert result is not None
        assert "emotion_state" in result
        assert "response_hint" in result

    def test_process_event_updates_soul(self, manager):
        """Test that event processing updates soul state."""
        soul = manager.create_npc(name="Update Test")
        
        event = GameEvent(GameEventType.QUEST_COMPLETED, intensity=1.0)
        manager.process_event(soul.npc_id, event)
        
        updated = manager.get_npc(soul.npc_id)
        assert len(updated.current_emotions) > 0

    def test_process_event_nonexistent_npc(self, manager):
        """Test processing event for non-existent NPC."""
        event = GameEvent(GameEventType.PLAYER_HELPED)
        
        with pytest.raises(ValueError):
            manager.process_event("nonexistent", event)


class TestGetEmotionState:
    """Tests for emotion state retrieval."""

    def test_get_emotion_state(self, manager):
        """Test getting emotion state."""
        soul = manager.create_npc(name="Emotion State Test")
        
        # Add some emotion
        event = GameEvent(GameEventType.QUEST_COMPLETED, intensity=1.0)
        manager.process_event(soul.npc_id, event)
        
        state = manager.get_emotion_state(soul.npc_id)
        
        assert "emotion_state" in state
        assert "composite_emotion" in state

    def test_get_emotion_state_empty(self, manager):
        """Test getting emotion state when empty."""
        soul = manager.create_npc(name="Empty Test")
        
        state = manager.get_emotion_state(soul.npc_id)
        
        assert state["emotion_state"] == {}


class TestGetBehavior:
    """Tests for behavior profile retrieval."""

    def test_get_behavior(self, manager):
        """Test getting behavior profile."""
        soul = manager.create_npc(name="Behavior Test")
        
        behavior = manager.get_behavior(soul.npc_id)
        
        assert "dialogue_style" in behavior
        assert "movement_pattern" in behavior
        assert "will_talk" in behavior


class TestClearEmotions:
    """Tests for emotion clearing."""

    def test_clear_emotions(self, manager):
        """Test clearing all emotions."""
        soul = manager.create_npc(name="Clear Test")
        
        # Add emotions
        event = GameEvent(GameEventType.QUEST_COMPLETED, intensity=1.0)
        manager.process_event(soul.npc_id, event)
        
        # Clear
        manager.clear_emotions(soul.npc_id)
        
        state = manager.get_emotion_state(soul.npc_id)
        assert len(state["emotion_state"]) == 0


class TestTick:
    """Tests for time-based emotion decay."""

    def test_tick_decay(self, manager):
        """Test emotion decay over time."""
        soul = manager.create_npc(name="Tick Test")
        
        # Add emotions
        event = GameEvent(GameEventType.QUEST_COMPLETED, intensity=1.0)
        manager.process_event(soul.npc_id, event)
        
        state_before = manager.get_emotion_state(soul.npc_id)
        joy_before = state_before["emotion_state"].get("joy", 0)
        
        # Tick forward
        manager.tick(soul.npc_id, delta_seconds=300.0)  # 5 minutes
        
        state_after = manager.get_emotion_state(soul.npc_id)
        joy_after = state_after["emotion_state"].get("joy", 0)
        
        assert joy_after < joy_before


class TestRelations:
    """Tests for relation management."""

    def test_add_relation(self, manager):
        """Test adding a relation."""
        soul = manager.create_npc(name="Relation Test")
        
        manager.add_relation(
            soul.npc_id,
            entity_id="player_001",
            relation_type="friend",
            weight=0.8,
        )
        
        relations = manager.get_relations(soul.npc_id)
        
        assert len(relations) > 0
        assert any(r["to"] == "player_001" for r in relations)


class TestPresets:
    """Tests for preset functionality."""

    def test_list_presets(self, manager):
        """Test listing presets."""
        presets = manager.list_presets()
        
        assert "tavern_keeper" in presets
        assert "guard_captain" in presets

    def test_get_preset_info(self, manager):
        """Test getting preset info."""
        info = manager.get_preset_info("tavern_keeper")
        
        assert info["name"] == "tavern_keeper"
        assert "personality" in info
        assert info["personality"]["extraversion"] == 0.8

    def test_get_nonexistent_preset(self, manager):
        """Test error on non-existent preset."""
        with pytest.raises(ValueError):
            manager.get_preset_info("nonexistent")


class TestFactoryFunction:
    """Tests for factory function."""

    def test_create_npc_manager(self, temp_npc_dir):
        """Test factory function."""
        manager = create_npc_manager(npc_dir=temp_npc_dir)
        
        assert isinstance(manager, NPCManager)


class TestPersistence:
    """Tests for NPC persistence."""

    def test_npc_persisted_to_file(self, manager, temp_npc_dir):
        """Test that NPC is saved to file."""
        soul = manager.create_npc(name="Persist Test", npc_id="persist-001")
        
        file_path = temp_npc_dir / "persist-001.yaml"
        assert file_path.exists()

    def test_npc_loaded_on_init(self, temp_npc_dir):
        """Test that NPCs are loaded when manager initializes."""
        # Create and save an NPC
        manager1 = NPCManager(npc_dir=temp_npc_dir)
        soul = manager1.create_npc(name="Load Test", npc_id="load-001")
        
        # Create new manager - should load existing NPC
        manager2 = NPCManager(npc_dir=temp_npc_dir)
        
        loaded = manager2.get_npc("load-001")
        assert loaded is not None
        assert loaded.name == "Load Test"

    def test_update_persisted(self, manager, temp_npc_dir):
        """Test that updates are persisted."""
        soul = manager.create_npc(name="Update Persist")
        
        # Process event to update
        event = GameEvent(GameEventType.QUEST_COMPLETED, intensity=1.0)
        manager.process_event(soul.npc_id, event)
        
        # Create new manager - should have updated state
        manager2 = NPCManager(npc_dir=temp_npc_dir)
        loaded = manager2.get_npc(soul.npc_id)
        
        assert len(loaded.current_emotions) > 0

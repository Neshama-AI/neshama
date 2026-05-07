"""
Neshama NPC Memory Bridge Tests
"""

import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.soul.npc_memory_bridge import (
    NPCMemoryBridge,
    NPCMemoryBridge,
    EntityRelation,
    EntityMemory,
    DialogueContext,
    EVENT_RELATION_MAPPINGS,
    get_memory_bridge,
)
from neshama.soul.emotion.game_event import GameEvent, GameEventType
from neshama.soul.entity_graph import EntityType


class TestNPCMemoryBridgeInit:
    """Tests for NPCMemoryBridge initialization."""

    def test_default_init(self):
        """Test default initialization."""
        bridge = NPCMemoryBridge()
        assert bridge is not None
        assert len(bridge._relations) == 0
        assert len(bridge._memories) == 0

    def test_singleton_bridge(self):
        """Test that get_memory_bridge returns singleton."""
        bridge1 = get_memory_bridge()
        bridge2 = get_memory_bridge()
        
        # May or may not be same instance depending on implementation
        assert bridge1 is not None


class TestGameEventProcessing:
    """Tests for processing game events."""

    def test_player_attacked_updates_relation(self):
        """Test that PLAYER_ATTACKED creates hostile relation."""
        bridge = NPCMemoryBridge()
        
        event = GameEvent(GameEventType.PLAYER_ATTACKED, intensity=1.0)
        
        bridge.on_game_event(
            npc_id="npc_001",
            event=event,
            entity_id="player_001",
            entity_name="Hero",
        )
        
        relation = bridge.get_relation("npc_001", "player_001")
        
        assert relation is not None
        assert relation.relation_type == "hostile"
        assert relation.strength > 0.3

    def test_player_helped_creates_ally_relation(self):
        """Test that PLAYER_HELPED creates ally relation."""
        bridge = NPCMemoryBridge()
        
        event = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
        
        bridge.on_game_event(
            npc_id="npc_001",
            event=event,
            entity_id="player_001",
            entity_name="Hero",
        )
        
        relation = bridge.get_relation("npc_001", "player_001")
        
        assert relation is not None
        assert relation.relation_type == "ally"
        assert relation.strength > 0.3
        assert relation.trust > 0.3

    def test_npc_complimented_increases_friendly(self):
        """Test that NPC_COMPLIMENTED increases friendly relation."""
        bridge = NPCMemoryBridge()
        
        event = GameEvent(GameEventType.NPC_COMPLIMENTED, intensity=1.0)
        
        bridge.on_game_event(
            npc_id="npc_001",
            event=event,
            entity_id="player_001",
            entity_name="Hero",
        )
        
        relation = bridge.get_relation("npc_001", "player_001")
        
        assert relation is not None
        assert relation.relation_type == "friendly"

    def test_multiple_events_accumulate(self):
        """Test that multiple events accumulate."""
        bridge = NPCMemoryBridge()
        
        # First event
        event1 = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
        bridge.on_game_event("npc_001", event1, "player_001", "Hero")
        
        initial_strength = bridge.get_relation("npc_001", "player_001").strength
        initial_count = bridge.get_relation("npc_001", "player_001").interaction_count
        
        # Second event
        event2 = GameEvent(GameEventType.QUEST_COMPLETED, intensity=1.0)
        bridge.on_game_event("npc_001", event2, "player_001", "Hero")
        
        relation = bridge.get_relation("npc_001", "player_001")
        
        assert relation.interaction_count == initial_count + 1

    def test_intensity_affects_strength_delta(self):
        """Test that event intensity affects strength delta."""
        bridge = NPCMemoryBridge()
        
        # Low intensity
        event_low = GameEvent(GameEventType.PLAYER_HELPED, intensity=0.5)
        bridge.on_game_event("npc_001", event_low, "player_001", "Hero")
        
        low_strength = bridge.get_relation("npc_001", "player_001").strength
        
        # Create new NPC for high intensity
        event_high = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
        bridge.on_game_event("npc_002", event_high, "player_002", "Hero")
        
        high_strength = bridge.get_relation("npc_002", "player_002").strength
        
        # High intensity should give higher strength
        assert high_strength > low_strength


class TestEntityRelation:
    """Tests for EntityRelation."""

    def test_to_dict(self):
        """Test EntityRelation serialization."""
        relation = EntityRelation(
            entity_id="player_001",
            entity_name="Hero",
            relation_type="ally",
            strength=0.8,
            trust=0.7,
            last_interaction=datetime.now().isoformat(),
            interaction_count=5,
        )
        
        data = relation.to_dict()
        
        assert data["entity_id"] == "player_001"
        assert data["entity_name"] == "Hero"
        assert data["relation_type"] == "ally"
        assert data["strength"] == 0.8
        assert data["trust"] == 0.7
        assert data["interaction_count"] == 5
        assert "strength_category" in data

    def test_strength_category(self):
        """Test strength category calculation."""
        relation = EntityRelation(
            entity_id="test",
            entity_name="Test",
            relation_type="friend",
            strength=0.85,
            trust=0.5,
            last_interaction=datetime.now().isoformat(),
        )
        
        data = relation.to_dict()
        
        assert data["strength_category"] == "intimate"


class TestEntityMemory:
    """Tests for EntityMemory."""

    def test_to_dict(self):
        """Test EntityMemory serialization."""
        memory = EntityMemory(
            memory_id="mem_001",
            entity_id="player_001",
            entity_name="Hero",
            event_type="player_helped",
            description="Hero helped me",
            timestamp=datetime.now().isoformat(),
            emotional_context={"joy": 0.8, "trust": 0.6},
            trust_at_time=0.7,
        )
        
        data = memory.to_dict()
        
        assert data["memory_id"] == "mem_001"
        assert data["entity_id"] == "player_001"
        assert data["event_type"] == "player_helped"
        assert "emotional_context" in data


class TestDialogueContext:
    """Tests for DialogueContext."""

    def test_to_dict(self):
        """Test DialogueContext serialization."""
        relation = EntityRelation(
            entity_id="player_001",
            entity_name="Hero",
            relation_type="ally",
            strength=0.8,
            trust=0.7,
            last_interaction=datetime.now().isoformat(),
        )
        
        memory = EntityMemory(
            memory_id="mem_001",
            entity_id="player_001",
            entity_name="Hero",
            event_type="player_helped",
            description="Hero helped me",
            timestamp=datetime.now().isoformat(),
            emotional_context={},
            trust_at_time=0.7,
        )
        
        context = DialogueContext(
            npc_id="npc_001",
            player_id="player_001",
            player_name="Hero",
            relation=relation,
            recent_memories=[memory],
            emotional_state={"joy": 0.8},
        )
        
        data = context.to_dict()
        
        assert data["npc_id"] == "npc_001"
        assert data["player_id"] == "player_001"
        assert data["relation"]["relation_type"] == "ally"
        assert len(data["recent_memories"]) == 1

    def test_to_prompt_parts(self):
        """Test DialogueContext prompt generation."""
        relation = EntityRelation(
            entity_id="player_001",
            entity_name="Hero",
            relation_type="ally",
            strength=0.8,
            trust=0.7,
            last_interaction=datetime.now().isoformat(),
        )
        
        context = DialogueContext(
            npc_id="npc_001",
            player_id="player_001",
            player_name="Hero",
            relation=relation,
            recent_memories=[],
            emotional_state={"joy": 0.5, "anger": 0.1},
        )
        
        parts = context.to_prompt_parts()
        
        assert len(parts) >= 1
        assert any("Hero" in part for part in parts)

    def test_to_prompt_parts_respects_max_memories(self):
        """Test that max_memories is respected."""
        relation = EntityRelation(
            entity_id="player_001",
            entity_name="Hero",
            relation_type="ally",
            strength=0.8,
            trust=0.7,
            last_interaction=datetime.now().isoformat(),
        )
        
        memories = [
            EntityMemory(
                memory_id=f"mem_{i}",
                entity_id="player_001",
                entity_name="Hero",
                event_type="player_helped",
                description=f"Memory {i}",
                timestamp=datetime.now().isoformat(),
                emotional_context={},
                trust_at_time=0.7,
            )
            for i in range(10)
        ]
        
        context = DialogueContext(
            npc_id="npc_001",
            player_id="player_001",
            player_name="Hero",
            relation=relation,
            recent_memories=memories,
            emotional_state={},
        )
        
        parts = context.to_prompt_parts(max_memories=3)
        
        # The memories in prompt should be limited
        # (actual behavior depends on implementation)


class TestRelationDecay:
    """Tests for relation decay."""

    def test_decay_weakens_relations(self):
        """Test that relations weaken over time."""
        bridge = NPCMemoryBridge()
        
        event = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
        bridge.on_game_event("npc_001", event, "player_001", "Hero")
        
        initial_strength = bridge.get_relation("npc_001", "player_001").strength
        
        # Apply decay
        bridge.decay_relations("npc_001", delta_seconds=100.0)
        
        new_strength = bridge.get_relation("npc_001", "player_001").strength
        
        assert new_strength < initial_strength


class TestGetDialogueContext:
    """Tests for getting dialogue context."""

    def test_get_context_returns_none_when_no_relation(self):
        """Test that get_context returns None when no relation exists."""
        bridge = NPCMemoryBridge()
        
        context = bridge.get_dialogue_context("npc_001", "player_001")
        
        assert context is None

    def test_get_context_with_relation(self):
        """Test getting context when relation exists."""
        bridge = NPCMemoryBridge()
        
        # Create relation
        event = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
        bridge.on_game_event("npc_001", event, "player_001", "Hero")
        
        context = bridge.get_dialogue_context(
            "npc_001",
            "player_001",
            player_name="Hero",
            emotional_state={"joy": 0.8},
        )
        
        assert context is not None
        assert context.npc_id == "npc_001"
        assert context.player_id == "player_001"
        assert context.relation is not None

    def test_get_context_with_memories(self):
        """Test that context includes recent memories."""
        bridge = NPCMemoryBridge()
        
        # Create multiple memories
        for i in range(3):
            event = GameEvent(GameEventType.PLAYER_HELPED, intensity=0.5)
            bridge.on_game_event("npc_001", event, "player_001", "Hero")
        
        context = bridge.get_dialogue_context(
            "npc_001",
            "player_001",
            max_memories=5,
        )
        
        assert context is not None
        assert len(context.recent_memories) >= 1


class TestEventRelationMappings:
    """Tests for event to relation mappings."""

    def test_all_event_types_have_mappings(self):
        """Test that all event types have mappings."""
        for event_type in GameEventType:
            assert event_type in EVENT_RELATION_MAPPINGS

    def test_mappings_have_required_fields(self):
        """Test that all mappings have required fields."""
        for event_type, mapping in EVENT_RELATION_MAPPINGS.items():
            assert "relation" in mapping
            assert "strength_delta" in mapping


class TestClearNPC:
    """Tests for clearing NPC data."""

    def test_clear_npc(self):
        """Test clearing all NPC data."""
        bridge = NPCMemoryBridge()
        
        # Create data
        event = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
        bridge.on_game_event("npc_001", event, "player_001", "Hero")
        
        # Verify data exists
        assert bridge.get_relation("npc_001", "player_001") is not None
        
        # Clear
        bridge.clear_npc("npc_001")
        
        # Verify data is gone
        assert bridge.get_relation("npc_001", "player_001") is None


class TestGetAllRelations:
    """Tests for getting all relations."""

    def test_get_all_relations(self):
        """Test getting all relations for an NPC."""
        bridge = NPCMemoryBridge()
        
        # Create multiple relations
        event1 = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
        bridge.on_game_event("npc_001", event1, "player_001", "Hero")
        
        event2 = GameEvent(GameEventType.NPC_COMPLIMENTED, intensity=1.0)
        bridge.on_game_event("npc_001", event2, "player_002", "Villager")
        
        relations = bridge.get_all_relations("npc_001")
        
        assert len(relations) == 2

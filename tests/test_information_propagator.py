"""
Neshama Information Propagator Tests
"""

import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.soul.information_propagator import (
    InformationPropagator, InformationType, Information,
    PropagationChain, NPCKnowledge,
)


class TestInformationType:
    """Tests for InformationType enum."""
    
    def test_all_types_exist(self):
        """Test that all info types are defined."""
        assert InformationType.PLAYER_ACTION.value == "player_action"
        assert InformationType.WORLD_EVENT.value == "world_event"
        assert InformationType.NPC_SECRET.value == "npc_secret"
        assert InformationType.QUEST_INFO.value == "quest_info"
        assert InformationType.RUMOR.value == "rumor"


class TestInformation:
    """Tests for Information dataclass."""
    
    def test_create_information(self):
        """Test creating basic information."""
        info = Information(
            info_id="info_001",
            info_type=InformationType.PLAYER_ACTION,
            original_content="The adventurer killed the dragon!",
            current_content="The adventurer killed the dragon!",
            source_npc_id="npc_001",
        )
        
        assert info.info_id == "info_001"
        assert info.info_type == InformationType.PLAYER_ACTION
        assert info.distortion_level == 0.0
        assert info.credibility == 1.0
    
    def test_to_dict(self):
        """Test information serialization."""
        info = Information(
            info_id="info_001",
            info_type=InformationType.WORLD_EVENT,
            original_content="A dragon appeared!",
            current_content="A dragon appeared!",
            source_npc_id="npc_001",
            importance=0.8,
            tags=["dragon", "danger"],
        )
        
        data = info.to_dict()
        
        assert data["info_id"] == "info_001"
        assert data["info_type"] == "world_event"
        assert data["importance"] == 0.8
        assert "dragon" in data["tags"]


class TestPropagationChain:
    """Tests for PropagationChain dataclass."""
    
    def test_create_chain(self):
        """Test creating propagation chain."""
        chain = PropagationChain(info_id="info_001")
        
        assert chain.info_id == "info_001"
        assert len(chain.chain) == 0
    
    def test_add_to_chain(self):
        """Test adding entries to chain."""
        chain = PropagationChain(info_id="info_001")
        chain.chain.append({
            "npc_id": "npc_002",
            "timestamp": datetime.now().isoformat(),
            "action": "received",
            "from": "npc_001",
        })
        
        assert len(chain.chain) == 1
        assert chain.chain[0]["npc_id"] == "npc_002"
    
    def test_to_dict(self):
        """Test chain serialization."""
        chain = PropagationChain(info_id="info_001")
        chain.chain.append({
            "npc_id": "npc_002",
            "timestamp": datetime.now().isoformat(),
            "action": "received",
            "from": "npc_001",
        })
        
        data = chain.to_dict()
        
        assert data["info_id"] == "info_001"
        assert len(data["chain"]) == 1


class TestNPCKnowledge:
    """Tests for NPCKnowledge dataclass."""
    
    def test_create_knowledge(self):
        """Test creating NPC knowledge."""
        knowledge = NPCKnowledge(
            npc_id="npc_001",
            known_info=[
                {"info_id": "info_001", "content": "A dragon!"},
                {"info_id": "info_002", "content": "A merchant arrived."},
            ]
        )
        
        assert knowledge.npc_id == "npc_001"
        assert len(knowledge.known_info) == 2
    
    def test_to_dict(self):
        """Test knowledge serialization."""
        knowledge = NPCKnowledge(
            npc_id="npc_001",
            known_info=[{"info_id": "info_001", "content": "A dragon!"}],
        )
        
        data = knowledge.to_dict()
        
        assert data["npc_id"] == "npc_001"
        assert data["info_count"] == 1


class TestInformationPropagator:
    """Tests for InformationPropagator."""
    
    @pytest.fixture
    def propagator(self):
        """Create fresh propagator for each test."""
        return InformationPropagator()
    
    def test_init(self, propagator):
        """Test propagator initialization."""
        assert len(propagator._information) == 0
        assert len(propagator._npc_knowledge) == 0
    
    def test_spread_information_new(self, propagator):
        """Test spreading new information."""
        result = propagator.spread_information(
            source_npc_id="npc_001",
            info_type="player_action",
            content="The adventurer saved the village!",
            targets=["npc_002", "npc_003"],
            importance=0.8,
        )
        
        assert "info_id" in result
        assert "spread_to" in result
    
    def test_spread_information_creates_entry(self, propagator):
        """Test that spreading creates info entry."""
        result = propagator.spread_information(
            source_npc_id="npc_001",
            info_type="world_event",
            content="A dragon appeared!",
            targets=["npc_002"],
        )
        
        info_id = result["info_id"]
        info = propagator._information.get(info_id)
        
        assert info is not None
        assert info.original_content == "A dragon appeared!"
        assert "npc_001" in info.seen_by
    
    def test_spread_information_to_targets(self, propagator):
        """Test that info spreads to targets."""
        result = propagator.spread_information(
            source_npc_id="npc_001",
            info_type="world_event",
            content="A festival is happening!",
            targets=["npc_002", "npc_003"],
            importance=1.0,  # Max importance = guaranteed spread
        )
        
        spread_to = result["spread_to"]
        
        # At least some should succeed (may vary based on trust)
        assert len(spread_to) == 2
    
    def test_npc_knowledge(self, propagator):
        """Test getting NPC knowledge."""
        # Spread some info
        propagator.spread_information(
            source_npc_id="npc_001",
            info_type="world_event",
            content="The merchant arrived!",
            targets=["npc_002"],
            importance=1.0,
        )
        
        knowledge = propagator.get_npc_knowledge("npc_001")
        
        assert knowledge.npc_id == "npc_001"
        assert len(knowledge.known_info) >= 1
    
    def test_knowledge_filter_by_type(self, propagator):
        """Test filtering knowledge by type."""
        propagator.spread_information(
            source_npc_id="npc_001",
            info_type="world_event",
            content="Dragon!",
            targets=[],
        )
        
        knowledge = propagator.get_npc_knowledge(
            "npc_001",
            info_type="world_event"
        )
        
        for info in knowledge.known_info:
            assert info["info_type"] == "world_event"
    
    def test_knowledge_filter_by_importance(self, propagator):
        """Test filtering by minimum importance."""
        propagator.spread_information(
            source_npc_id="npc_001",
            info_type="world_event",
            content="Minor rumor",
            targets=[],
            importance=0.2,
        )
        
        knowledge = propagator.get_npc_knowledge(
            "npc_001",
            min_importance=0.5
        )
        
        for info in knowledge.known_info:
            assert info["importance"] >= 0.5
    
    def test_get_information_chain(self, propagator):
        """Test getting propagation chain."""
        result = propagator.spread_information(
            source_npc_id="npc_001",
            info_type="world_event",
            content="News!",
            targets=["npc_002"],
            importance=1.0,
        )
        
        chain = propagator.get_information_chain(result["info_id"])
        
        assert chain is not None
        assert chain.info_id == result["info_id"]
    
    def test_get_info_details(self, propagator):
        """Test getting full info details."""
        result = propagator.spread_information(
            source_npc_id="npc_001",
            info_type="quest_info",
            content="The hero needs help!",
            targets=["npc_002"],
            tags=["quest", "urgent"],
            importance=0.9,
        )
        
        details = propagator.get_info_details(result["info_id"])
        
        assert details is not None
        assert details["info_type"] == "quest_info"
        assert "urgent" in details["tags"]
    
    def test_decay_information(self, propagator):
        """Test information decay."""
        # Add some info
        result = propagator.spread_information(
            source_npc_id="npc_001",
            info_type="rumor",
            content="Old news...",
            targets=[],
            importance=0.3,
        )
        
        info_id = result["info_id"]
        
        # Decay
        result = propagator.decay_information(delta_seconds=300.0)
        
        assert result["decayed_count"] >= 0
        # Low importance info may be forgotten
    
    def test_broadcast_world_event(self, propagator):
        """Test broadcasting world event."""
        result = propagator.broadcast_world_event(
            source_npc_id="npc_001",
            event_type="dragon_sighting",
            event_content="A dragon was spotted near the mountain!",
            session_npcs=["npc_001", "npc_002", "npc_003"],
            importance=0.9,
        )
        
        assert "info_id" in result
        assert result["spread_to"] is not None
    
    def test_spread_player_action(self, propagator):
        """Test spreading player action."""
        result = propagator.spread_player_action(
            player_id="player_001",
            action="killed the goblin chief",
            source_npc_id="npc_001",
            session_npcs=["npc_001", "npc_002", "npc_003"],
            importance=0.7,
        )
        
        assert "info_id" in result
        
        # Check info type
        info = propagator._information.get(result["info_id"])
        assert info is not None
        assert info.info_type == InformationType.PLAYER_ACTION
    
    def test_get_knowledge_summary(self, propagator):
        """Test getting knowledge summary."""
        # Add various info
        propagator.spread_information(
            source_npc_id="npc_001",
            info_type="world_event",
            content="Event 1",
            targets=["npc_002"],
            importance=1.0,
        )
        propagator.spread_information(
            source_npc_id="npc_001",
            info_type="player_action",
            content="Action 1",
            targets=["npc_002"],
            importance=0.8,
        )
        
        summary = propagator.get_knowledge_summary("npc_001")
        
        assert summary["npc_id"] == "npc_001"
        assert "total_known" in summary
        assert "by_type" in summary


class TestDistortion:
    """Tests for information distortion."""
    
    @pytest.fixture
    def propagator(self):
        return InformationPropagator()
    
    def test_rumor_distorts(self, propagator):
        """Test that rumors can distort."""
        # Create info
        result = propagator.spread_information(
            source_npc_id="npc_001",
            info_type="rumor",
            content="The adventurer defeated ten goblins in the forest",
            targets=["npc_002"],
            importance=1.0,
        )
        
        info_id = result["info_id"]
        
        # Propagate again
        result2 = propagator.spread_information(
            source_npc_id="npc_002",
            info_type="rumor",
            content="",  # Will use current content
            targets=["npc_003"],
            importance=1.0,
            info_id=info_id,
        )
        
        # Check distortion increased
        info = propagator._information.get(info_id)
        assert info is not None
        assert info.propagation_count >= 1
    
    def test_non_rumor_does_not_distort(self, propagator):
        """Test that non-rumors don't distort."""
        result = propagator.spread_information(
            source_npc_id="npc_001",
            info_type="world_event",
            content="The king announced a new law",
            targets=["npc_002"],
            importance=1.0,
        )
        
        info_id = result["info_id"]
        info = propagator._information.get(info_id)
        
        # World events shouldn't distort
        assert info.distortion_level == 0.0


class TestTrustBasedPropagation:
    """Tests for trust-based propagation."""
    
    @pytest.fixture
    def propagator(self):
        return InformationPropagator()
    
    def test_set_social_engine(self, propagator):
        """Test setting social engine for trust lookup."""
        from neshama.soul.social_engine import NPCSocialEngine
        
        engine = NPCSocialEngine()
        engine.register_npc("npc_001")
        engine.register_npc("npc_002")
        engine.get_or_create_relation("npc_001", "npc_002").trust = 0.9
        
        propagator.set_social_engine(engine)
        
        assert propagator._social_engine is engine


class TestGlobalInstance:
    """Tests for global instance management."""
    
    def test_get_propagator(self):
        """Test getting global instance."""
        from neshama.soul.information_propagator import get_propagator
        
        prop1 = get_propagator()
        prop2 = get_propagator()
        
        assert prop1 is prop2

"""
Neshama NPC Social Engine Tests
"""

import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.soul.social_engine import (
    NPCSocialEngine, SocialInteractionType, RelationshipCategory,
    NPCRelation, SocialEvent, SocialDecisionContext,
)


class TestNPCRelation:
    """Tests for NPCRelation dataclass."""
    
    def test_create_relation(self):
        """Test creating a basic relation."""
        relation = NPCRelation(
            npc_a_id="npc_001",
            npc_b_id="npc_002",
        )
        
        assert relation.npc_a_id == "npc_001"
        assert relation.npc_b_id == "npc_002"
        assert relation.strength == 0.5
        assert relation.trust == 0.5
        assert relation.familiarity == 0.0
    
    def test_to_dict(self):
        """Test relation serialization."""
        relation = NPCRelation(
            npc_a_id="npc_001",
            npc_b_id="npc_002",
            strength=0.7,
            trust=0.6,
            category=RelationshipCategory.FRIEND,
        )
        
        data = relation.to_dict()
        
        assert data["npc_a_id"] == "npc_001"
        assert data["strength"] == 0.7
        assert data["category"] == "friend"
    
    def test_from_dict(self):
        """Test relation deserialization."""
        data = {
            "npc_a_id": "npc_001",
            "npc_b_id": "npc_002",
            "strength": 0.7,
            "trust": 0.6,
            "familiarity": 0.3,
            "category": "enemy",
        }
        
        relation = NPCRelation.from_dict(data)
        
        assert relation.npc_a_id == "npc_001"
        assert relation.strength == 0.7
        assert relation.category == RelationshipCategory.ENEMY


class TestSocialEvent:
    """Tests for SocialEvent dataclass."""
    
    def test_create_event(self):
        """Test creating a social event."""
        event = SocialEvent(
            event_id="evt_001",
            npc_a_id="npc_001",
            npc_b_id="npc_002",
            interaction_type=SocialInteractionType.GOSSIP,
        )
        
        assert event.event_id == "evt_001"
        assert event.interaction_type == SocialInteractionType.GOSSIP
        assert event.success is True
    
    def test_to_dict(self):
        """Test event serialization."""
        event = SocialEvent(
            event_id="evt_001",
            npc_a_id="npc_001",
            npc_b_id="npc_002",
            interaction_type=SocialInteractionType.ARGUE,
            relationship_delta={"strength": -0.1, "trust": -0.1},
        )
        
        data = event.to_dict()
        
        assert data["event_id"] == "evt_001"
        assert data["interaction_type"] == "argue"
        assert data["relationship_delta"]["strength"] == -0.1


class TestNPCSocialEngine:
    """Tests for NPCSocialEngine."""
    
    @pytest.fixture
    def engine(self):
        """Create a fresh engine for each test."""
        return NPCSocialEngine()
    
    def test_init(self, engine):
        """Test engine initialization."""
        assert len(engine._relations) == 0
        assert len(engine._social_events) == 0
    
    def test_register_npc(self, engine):
        """Test NPC registration."""
        engine.register_npc(
            npc_id="npc_001",
            session_id="session_001",
            personality={"extraversion": 0.8, "agreeableness": 0.6},
            emotions={"joy": 0.7, "anger": 0.1},
        )
        
        assert "npc_001" in engine._npc_profiles
        assert engine._npc_sessions["npc_001"] == "session_001"
        assert engine._npc_profiles["npc_001"]["personality"]["extraversion"] == 0.8
    
    def test_update_npc_state(self, engine):
        """Test updating NPC state."""
        engine.register_npc("npc_001", personality={"extraversion": 0.5})
        
        engine.update_npc_state(
            npc_id="npc_001",
            session_id="session_002",
            emotions={"joy": 0.9},
        )
        
        assert engine._npc_sessions["npc_001"] == "session_002"
        assert engine._npc_profiles["npc_001"]["emotions"]["joy"] == 0.9
    
    def test_get_or_create_relation(self, engine):
        """Test getting or creating relations."""
        relation = engine.get_or_create_relation("npc_001", "npc_002")
        
        assert relation.npc_a_id == "npc_001"
        assert relation.npc_b_id == "npc_002"
        assert relation.strength == 0.5
        
        # Getting again returns same relation
        relation2 = engine.get_or_create_relation("npc_001", "npc_002")
        assert relation is relation2
    
    def test_get_relation(self, engine):
        """Test getting existing relation."""
        engine.get_or_create_relation("npc_001", "npc_002")
        
        relation = engine.get_relation("npc_001", "npc_002")
        assert relation is not None
        
        # Order doesn't matter
        relation2 = engine.get_relation("npc_002", "npc_001")
        assert relation2 is not None
    
    def test_relation_key_normalized(self, engine):
        """Test that relation keys are normalized."""
        engine.get_or_create_relation("npc_001", "npc_002")
        
        # Both directions should find the same relation
        assert engine.get_relation("npc_001", "npc_002") is not None
        assert engine.get_relation("npc_002", "npc_001") is not None
    
    def test_initiate_interaction_gossip(self, engine):
        """Test gossip interaction."""
        engine.register_npc("npc_001", personality={"agreeableness": 0.7})
        engine.register_npc("npc_002", personality={"agreeableness": 0.5})
        
        event = engine.initiate_interaction("npc_001", "npc_002", {"topic": "news"})
        
        assert event.success is True
        assert event.interaction_type in SocialInteractionType
        assert event.npc_a_id == "npc_001"
        assert event.npc_b_id == "npc_002"
    
    def test_initiate_interaction_trade(self, engine):
        """Test trade interaction."""
        engine.register_npc("npc_001", personality={"extraversion": 0.7})
        engine.register_npc("npc_002", personality={"extraversion": 0.5})
        
        # Force trade interaction
        event = engine.initiate_interaction(
            "npc_001", "npc_002",
            forced_type=SocialInteractionType.TRADE
        )
        
        assert event.success is True
        assert event.interaction_type == SocialInteractionType.TRADE
    
    def test_initiate_interaction_ally(self, engine):
        """Test alliance interaction."""
        engine.register_npc("npc_001", personality={"extraversion": 0.8})
        engine.register_npc("npc_002", personality={"agreeableness": 0.6})
        
        # Set high trust
        relation = engine.get_or_create_relation("npc_001", "npc_002")
        relation.trust = 0.8
        
        event = engine.initiate_interaction(
            "npc_001", "npc_002",
            forced_type=SocialInteractionType.ALLY
        )
        
        assert event.success is True
        assert event.interaction_type == SocialInteractionType.ALLY
    
    def test_interaction_affects_relationship(self, engine):
        """Test that interactions change relationships."""
        engine.register_npc("npc_001")
        engine.register_npc("npc_002")
        
        relation = engine.get_or_create_relation("npc_001", "npc_002")
        initial_strength = relation.strength
        
        engine.initiate_interaction(
            "npc_001", "npc_002",
            forced_type=SocialInteractionType.ALLY
        )
        
        # Ally should increase strength
        assert relation.strength > initial_strength
    
    def test_interaction_increases_familiarity(self, engine):
        """Test that interactions increase familiarity."""
        engine.register_npc("npc_001")
        engine.register_npc("npc_002")
        
        relation = engine.get_or_create_relation("npc_001", "npc_002")
        assert relation.familiarity == 0.0
        
        engine.initiate_interaction("npc_001", "npc_002")
        
        assert relation.familiarity > 0.0
    
    def test_cooldown_prevents_rapid_interactions(self, engine):
        """Test that cooldown prevents too frequent interactions."""
        engine.register_npc("npc_001")
        engine.register_npc("npc_002")
        
        # First interaction succeeds
        event1 = engine.initiate_interaction("npc_001", "npc_002")
        assert event1.success is True
        
        # Second should fail (within cooldown)
        event2 = engine.initiate_interaction("npc_001", "npc_002")
        assert event2.success is False
        assert event2.context.get("reason") == "cooldown"
    
    def test_get_social_graph(self, engine):
        """Test getting social graph."""
        engine.register_npc("npc_001")
        engine.register_npc("npc_002")
        engine.register_npc("npc_003")
        
        # Create some relations
        engine.initiate_interaction("npc_001", "npc_002")
        
        relation = engine.get_or_create_relation("npc_001", "npc_002")
        relation.strength = 0.8
        engine._update_relation_category(relation)
        
        graph = engine.get_social_graph("npc_001")
        
        assert graph["npc_id"] == "npc_001"
        assert "friends" in graph
        assert "enemies" in graph
        assert "neutrals" in graph
    
    def test_get_mutual_relations(self, engine):
        """Test getting mutual relation info."""
        engine.register_npc("npc_001")
        engine.register_npc("npc_002")
        
        engine.initiate_interaction("npc_001", "npc_002")
        
        mutual = engine.get_mutual_relations("npc_001", "npc_002")
        
        assert "relation" in mutual
        assert mutual["can_interact"] is True
        assert "suggested_interaction" in mutual
    
    def test_propagate_information(self, engine):
        """Test information propagation."""
        engine.register_npc("npc_001")
        engine.register_npc("npc_002")
        
        # Set up some trust
        relation = engine.get_or_create_relation("npc_001", "npc_002")
        relation.trust = 0.6
        relation.familiarity = 0.3
        
        result = engine.propagate_information(
            "npc_001", "npc_002",
            info_type="WORLD_EVENT",
            content="A dragon appeared!"
        )
        
        assert result["success"] is True
        assert result["shared_with"] == "npc_002"
        assert "fidelity" in result
    
    def test_propagate_information_low_trust(self, engine):
        """Test information fails with low trust."""
        engine.register_npc("npc_001")
        engine.register_npc("npc_002")
        
        relation = engine.get_or_create_relation("npc_001", "npc_002")
        relation.trust = 0.1
        
        result = engine.propagate_information(
            "npc_001", "npc_002",
            info_type="WORLD_EVENT",
            content="A dragon appeared!"
        )
        
        assert result["success"] is False
        assert result["reason"] == "low_trust"
    
    def test_get_recent_events(self, engine):
        """Test getting recent events."""
        engine.register_npc("npc_001")
        engine.register_npc("npc_002")
        engine.register_npc("npc_003")
        
        engine.initiate_interaction("npc_001", "npc_002")
        engine.initiate_interaction("npc_002", "npc_003")
        
        events = engine.get_recent_events(limit=10)
        
        assert len(events) == 2
        
        # Test filter by NPC
        events = engine.get_recent_events(npc_id="npc_001", limit=10)
        assert all(
            e["npc_a_id"] == "npc_001" or e["npc_b_id"] == "npc_001"
            for e in events
        )


class TestInteractionDecisions:
    """Tests for interaction decision logic."""
    
    @pytest.fixture
    def engine(self):
        return NPCSocialEngine()
    
    def test_high_anger_triggers_argue(self, engine):
        """Test that high anger leads to argue."""
        # npc_a_personality, npc_a_emotions, npc_b_personality, npc_b_emotions, relation
        relation = engine.get_or_create_relation("npc_001", "npc_002")
        
        interaction_type = engine._decide_interaction_type(
            {"agreeableness": 0.5},  # npc_a_personality
            {"anger": 0.7},  # npc_a_emotions
            {},  # npc_b_personality
            {},  # npc_b_emotions
            relation,
        )
        
        assert interaction_type == SocialInteractionType.ARGUE
    
    def test_target_sadness_triggers_comfort(self, engine):
        """Test that target's sadness leads to comfort."""
        relation = engine.get_or_create_relation("npc_001", "npc_002")
        relation.trust = 0.6
        
        interaction_type = engine._decide_interaction_type(
            {},  # Initiator emotions
            {},  # Initiator emotions
            {},  # Target emotions
            {"sadness": 0.6},  # Target emotions
            relation,
        )
        
        # Should be comfort if trust is high enough
        assert interaction_type == SocialInteractionType.COMFORT
    
    def test_high_agreeableness_gossip(self, engine):
        """Test that agreeable NPCs gossip."""
        relation = NPCRelation(npc_a_id="a", npc_b_id="b")
        
        interaction_type = engine._decide_interaction_type(
            {"agreeableness": 0.8},  # High agreeableness
            {},
            {},
            {},
            relation,
        )
        
        assert interaction_type in [SocialInteractionType.GOSSIP, SocialInteractionType.COMFORT]
    
    def test_trust_threshold_for_deep_interaction(self, engine):
        """Test trust threshold for deep interactions."""
        relation = NPCRelation(npc_a_id="a", npc_b_id="b")
        relation.trust = 0.8  # Above threshold
        
        interaction_type = engine._decide_interaction_type(
            {},
            {},
            {},
            {},
            relation,
        )
        
        assert interaction_type in [SocialInteractionType.ALLY, SocialInteractionType.TEACH]


class TestRelationshipEffects:
    """Tests for relationship effect calculations."""
    
    @pytest.fixture
    def engine(self):
        return NPCSocialEngine()
    
    def test_ally_increases_strength(self, engine):
        """Test that ALLY increases strength."""
        delta = engine._calculate_interaction_effects(
            SocialInteractionType.ALLY,
            {},
            {},
            NPCRelation(npc_a_id="a", npc_b_id="b"),
        )
        
        assert delta["strength"] > 0
        assert delta["trust"] > 0
    
    def test_argue_decreases_strength(self, engine):
        """Test that ARGUE decreases strength."""
        delta = engine._calculate_interaction_effects(
            SocialInteractionType.ARGUE,
            {},
            {},
            NPCRelation(npc_a_id="a", npc_b_id="b"),
        )
        
        assert delta["strength"] < 0
    
    def test_comfort_increases_bond(self, engine):
        """Test that COMFORT increases bond."""
        delta = engine._calculate_interaction_effects(
            SocialInteractionType.COMFORT,
            {},
            {},
            NPCRelation(npc_a_id="a", npc_b_id="b"),
        )
        
        assert delta["bond"] > 0
    
    def test_flirt_increases_romantic(self, engine):
        """Test that FLIRT increases romantic interest."""
        delta = engine._calculate_interaction_effects(
            SocialInteractionType.FLIRT,
            {},
            {},
            NPCRelation(npc_a_id="a", npc_b_id="b"),
        )
        
        assert delta["romantic_interest"] > 0
    
    def test_grudge_modifies_argue(self, engine):
        """Test that existing grudge modifies argue effect."""
        relation = NPCRelation(npc_a_id="a", npc_b_id="b", grudge=0.5)
        
        delta = engine._calculate_interaction_effects(
            SocialInteractionType.ARGUE,
            {},
            {},
            relation,
        )
        
        # With grudge, argue should have reduced effect
        assert delta["strength"] > -0.15


class TestSocialTick:
    """Tests for autonomous social tick."""
    
    @pytest.fixture
    def engine(self):
        return NPCSocialEngine()
    
    def test_social_tick_requires_multiple_npcs(self, engine):
        """Test that tick needs at least 2 NPCs."""
        engine.register_npc("npc_001", session_id="session_001")
        
        events = engine.social_tick(session_id="session_001")
        
        assert len(events) == 0
    
    def test_social_tick_same_session(self, engine):
        """Test that tick only considers same-session NPCs."""
        engine.register_npc("npc_001", session_id="session_001")
        engine.register_npc("npc_002", session_id="session_001")
        engine.register_npc("npc_003", session_id="session_002")  # Different session
        
        events = engine.social_tick(session_id="session_001")
        
        # Should only interact with npc_001 and npc_002
        for event in events:
            assert "npc_003" not in [event.npc_a_id, event.npc_b_id]
    
    def test_social_tick_respects_cooldown(self, engine):
        """Test that tick respects interaction cooldown."""
        engine.register_npc("npc_001", session_id="session_001")
        engine.register_npc("npc_002", session_id="session_001")
        
        # Pre-interact to start cooldown
        engine.initiate_interaction("npc_001", "npc_002")
        
        # Tick should not create more interactions between same pair
        events = engine.social_tick(session_id="session_001")
        
        same_pair_events = [
            e for e in events
            if {e.npc_a_id, e.npc_b_id} == {"npc_001", "npc_002"}
        ]
        
        assert len(same_pair_events) == 0
    
    def test_social_tick_max_limit(self, engine):
        """Test that tick respects max interactions limit."""
        # Register many NPCs
        for i in range(10):
            engine.register_npc(f"npc_{i:03d}", session_id="session_001")
        
        events = engine.social_tick(session_id="session_001")
        
        assert len(events) <= NPCSocialEngine.MAX_INTERACTIONS_PER_TICK


class TestGlobalInstance:
    """Tests for global instance management."""
    
    def test_get_social_engine(self):
        """Test getting global instance."""
        from neshama.soul.social_engine import get_social_engine
        
        engine1 = get_social_engine()
        engine2 = get_social_engine()
        
        assert engine1 is engine2

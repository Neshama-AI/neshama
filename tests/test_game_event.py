"""
Neshama Game Event Engine Tests
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.soul.emotion.game_event import (
    GameEventEngine,
    GameEvent,
    GameEventType,
    EmotionDelta,
    EventChainResult,
    EVENT_EMOTION_MAPPINGS,
    create_game_event_engine,
)


class TestGameEventTypes:
    """Tests for GameEventType enum."""

    def test_all_event_types_exist(self):
        """All 15 event types should be defined."""
        expected_types = [
            "player_attacked",
            "player_helped",
            "item_received",
            "item_lost",
            "quest_completed",
            "quest_failed",
            "npc_insulted",
            "npc_complimented",
            "environment_changed",
            "relationship_changed",
            "time_passed",
            "combat_started",
            "combat_ended",
            "death_witnessed",
            "gift_given",
        ]
        actual_types = [e.value for e in GameEventType]
        assert set(expected_types) == set(actual_types)

    def test_event_type_from_string(self):
        """Event types should be creatable from strings."""
        event_type = GameEventType("player_attacked")
        assert event_type == GameEventType.PLAYER_ATTACKED


class TestGameEvent:
    """Tests for GameEvent dataclass."""

    def test_create_event(self):
        """Test basic event creation."""
        event = GameEvent(GameEventType.PLAYER_HELPED)
        assert event.event_type == GameEventType.PLAYER_HELPED
        assert event.intensity == 1.0

    def test_event_intensity_bounds(self):
        """Test intensity is clamped to 0-1."""
        event = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.5)
        assert event.intensity == 1.0
        
        event = GameEvent(GameEventType.PLAYER_HELPED, intensity=-0.5)
        assert event.intensity == 0.0

    def test_event_with_context(self):
        """Test event with context data."""
        event = GameEvent(
            GameEventType.ITEM_RECEIVED,
            intensity=0.8,
            context={"item_id": "sword_001", "rarity": "rare"},
        )
        assert event.context["item_id"] == "sword_001"


class TestGameEventEngine:
    """Tests for GameEventEngine."""

    def test_default_init(self):
        """Test engine initialization."""
        engine = GameEventEngine()
        assert engine.personality is not None
        assert len(engine.personality) == 5

    def test_custom_personality_init(self):
        """Test engine with custom personality."""
        personality = {
            "openness": 0.7,
            "conscientiousness": 0.8,
            "extraversion": 0.6,
            "agreeableness": 0.5,
            "neuroticism": 0.3,
        }
        engine = GameEventEngine(personality=personality)
        assert engine.personality["openness"] == 0.7

    def test_process_player_attacked(self):
        """Test player_attacked event generates anger and fear."""
        engine = GameEventEngine()
        event = GameEvent(GameEventType.PLAYER_ATTACKED, intensity=1.0)
        deltas = engine.process_event(event)
        
        emotion_names = [d.emotion for d in deltas]
        assert "anger" in emotion_names
        assert "fear" in emotion_names
        
        # Find anger delta
        anger_delta = next(d for d in deltas if d.emotion == "anger")
        assert anger_delta.scaled_by_intensity == 0.3

    def test_process_player_helped(self):
        """Test player_helped event generates trust and joy."""
        engine = GameEventEngine()
        event = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
        deltas = engine.process_event(event)
        
        emotion_names = [d.emotion for d in deltas]
        assert "trust" in emotion_names
        assert "joy" in emotion_names

    def test_intensity_scaling(self):
        """Test that intensity scales deltas correctly."""
        engine = GameEventEngine()
        
        # Full intensity
        event_full = GameEvent(GameEventType.PLAYER_ATTACKED, intensity=1.0)
        deltas_full = engine.process_event(event_full)
        anger_full = next(d for d in deltas_full if d.emotion == "anger")
        
        # Half intensity
        event_half = GameEvent(GameEventType.PLAYER_ATTACKED, intensity=0.5)
        deltas_half = engine.process_event(event_half)
        anger_half = next(d for d in deltas_half if d.emotion == "anger")
        
        assert anger_half.scaled_by_intensity == pytest.approx(anger_full.scaled_by_intensity * 0.5)

    def test_quest_completed_generates_pride(self):
        """Test quest_completed includes pride emotion."""
        engine = GameEventEngine()
        event = GameEvent(GameEventType.QUEST_COMPLETED, intensity=1.0)
        deltas = engine.process_event(event)
        
        emotion_names = [d.emotion for d in deltas]
        assert "joy" in emotion_names
        assert "pride" in emotion_names

    def test_death_witnessed_generates_sadness_and_fear(self):
        """Test death_witnessed generates strong negative emotions."""
        engine = GameEventEngine()
        event = GameEvent(GameEventType.DEATH_WITNESSED, intensity=1.0)
        deltas = engine.process_event(event)
        
        emotion_names = [d.emotion for d in deltas]
        assert "sadness" in emotion_names
        assert "fear" in emotion_names
        
        # Sadness should be dominant
        sadness_delta = next(d for d in deltas if d.emotion == "sadness")
        assert sadness_delta.scaled_by_intensity == 0.4

    def test_gift_given_generates_joy_and_trust(self):
        """Test gift_given generates positive emotions."""
        engine = GameEventEngine()
        event = GameEvent(GameEventType.GIFT_GIVEN, intensity=1.0)
        deltas = engine.process_event(event)
        
        emotion_names = [d.emotion for d in deltas]
        assert "joy" in emotion_names
        assert "trust" in emotion_names

    def test_npc_insulted_generates_anger(self):
        """Test npc_insulted generates strong anger."""
        engine = GameEventEngine()
        event = GameEvent(GameEventType.NPC_INSULTED, intensity=1.0)
        deltas = engine.process_event(event)
        
        emotion_names = [d.emotion for d in deltas]
        assert "anger" in emotion_names
        assert "disgust" in emotion_names
        
        anger_delta = next(d for d in deltas if d.emotion == "anger")
        assert anger_delta.scaled_by_intensity == 0.4

    def test_all_event_types_processable(self):
        """All 15 event types should be processable."""
        engine = GameEventEngine()
        for event_type in GameEventType:
            event = GameEvent(event_type, intensity=0.5)
            deltas = engine.process_event(event)
            assert len(deltas) > 0, f"No deltas for {event_type}"

    def test_personality_modifier_agreeableness(self):
        """Test high agreeableness reduces anger response to insults."""
        # Low agreeableness
        low_agree = GameEventEngine(personality={"agreeableness": 0.2, "neuroticism": 0.5})
        event = GameEvent(GameEventType.NPC_INSULTED, intensity=1.0)
        deltas_low = low_agree.process_event(event)
        anger_low = next(d for d in deltas_low if d.emotion == "anger")
        
        # High agreeableness
        high_agree = GameEventEngine(personality={"agreeableness": 0.8, "neuroticism": 0.5})
        deltas_high = high_agree.process_event(event)
        anger_high = next(d for d in deltas_high if d.emotion == "anger")
        
        # High agreeableness should reduce anger (base 0.4 * 0.5 = 0.2)
        assert anger_high.scaled_by_intensity < anger_low.scaled_by_intensity

    def test_personality_modifier_neuroticism(self):
        """Test high neuroticism amplifies emotional responses."""
        low_neuro = GameEventEngine(personality={"agreeableness": 0.5, "neuroticism": 0.2})
        event = GameEvent(GameEventType.DEATH_WITNESSED, intensity=1.0)
        deltas_low = low_neuro.process_event(event)
        sadness_low = next(d for d in deltas_low if d.emotion == "sadness")
        
        high_neuro = GameEventEngine(personality={"agreeableness": 0.5, "neuroticism": 0.8})
        deltas_high = high_neuro.process_event(event)
        sadness_high = next(d for d in deltas_high if d.emotion == "sadness")
        
        # High neuroticism should amplify sadness
        assert sadness_high.scaled_by_intensity > sadness_low.scaled_by_intensity

    def test_get_event_info(self):
        """Test getting info about specific event."""
        engine = GameEventEngine()
        info = engine.get_event_info(GameEventType.QUEST_COMPLETED)
        
        assert info["event_type"] == "quest_completed"
        assert "joy" in info["affected_emotions"]
        assert "pride" in info["affected_emotions"]

    def test_list_all_events(self):
        """Test listing all events."""
        engine = GameEventEngine()
        events = engine.list_all_events()
        
        assert len(events) == 15
        assert all("event_type" in e for e in events)
        assert all("affected_emotions" in e for e in events)


class TestEventChain:
    """Tests for event chain processing."""

    def test_process_chain(self):
        """Test processing multiple events as a chain."""
        engine = GameEventEngine()
        
        events = [
            GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0),
            GameEvent(GameEventType.GIFT_GIVEN, intensity=0.8),
        ]
        
        result = engine.process_chain(events, "chain_001")
        
        assert isinstance(result, EventChainResult)
        assert result.chain_id == "chain_001"
        assert result.event_count == 2
        
        # Trust should accumulate
        trust_deltas = [d for d in result.total_deltas if d.emotion == "trust"]
        assert len(trust_deltas) > 0

    def test_chain_accumulates_emotions(self):
        """Test that repeated events accumulate emotion."""
        engine = GameEventEngine()
        
        events = [
            GameEvent(GameEventType.QUEST_COMPLETED, intensity=1.0),
            GameEvent(GameEventType.QUEST_COMPLETED, intensity=1.0),
        ]
        
        result = engine.process_chain(events, "quest_chain")
        
        # Joy should accumulate
        joy_total = sum(
            d.scaled_by_intensity 
            for d in result.total_deltas 
            if d.emotion == "joy"
        )
        assert joy_total > 0.4  # Should be 0.4 * 2 = 0.8

    def test_chain_dominant_emotion(self):
        """Test dominant emotion calculation in chains."""
        engine = GameEventEngine()
        
        events = [
            GameEvent(GameEventType.QUEST_COMPLETED, intensity=1.0),  # joy + pride
            GameEvent(GameEventType.NPC_COMPLIMENTED, intensity=1.0),  # joy + trust
        ]
        
        result = engine.process_chain(events, "mixed_chain")
        
        # Joy should be dominant (appears in both events)
        assert result.dominant_emotion == "joy"


class TestFactoryFunction:
    """Tests for factory function."""

    def test_create_game_event_engine(self):
        """Test factory function creates engine."""
        engine = create_game_event_engine()
        assert isinstance(engine, GameEventEngine)

    def test_create_with_personality(self):
        """Test factory with custom personality."""
        personality = {"agreeableness": 0.9}
        engine = create_game_event_engine(personality=personality)
        assert engine.personality["agreeableness"] == 0.9

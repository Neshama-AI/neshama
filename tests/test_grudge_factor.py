# Tests for Game Event Engine Grudge Factor
"""
Tests for the grudge factor that reduces positive emotion deltas
when an NPC has a negative relationship with the event source.
"""

import pytest

from neshama.soul.emotion.game_event import (
    GameEventEngine,
    GameEvent,
    GameEventType,
    EmotionDelta,
    POSITIVE_EMOTIONS,
    RELATIONSHIP_GRUDGE_MAP,
)


class TestGrudgeFactorConstants:
    """Tests for grudge factor constants."""
    
    def test_hostile_grudge(self):
        """Hostile relationship should have 0.5 grudge factor."""
        assert RELATIONSHIP_GRUDGE_MAP["hostile"] == 0.5
    
    def test_enemy_grudge(self):
        """Enemy relationship should have 0.6 grudge factor."""
        assert RELATIONSHIP_GRUDGE_MAP["enemy"] == 0.6
    
    def test_neutral_no_grudge(self):
        """Neutral relationship should have no grudge factor."""
        assert RELATIONSHIP_GRUDGE_MAP["neutral"] == 0.0
    
    def test_friendly_no_grudge(self):
        """Friendly relationship should have no grudge factor."""
        assert RELATIONSHIP_GRUDGE_MAP["friendly"] == 0.0
    
    def test_positive_emotions_set(self):
        """POSITIVE_EMOTIONS should include joy and trust."""
        assert "joy" in POSITIVE_EMOTIONS
        assert "trust" in POSITIVE_EMOTIONS


class TestGrudgeFactorProcessEvent:
    """Tests for grudge factor in process_event."""
    
    def test_no_grudge_by_default(self):
        """Without relationship_type, no grudge factor should apply."""
        engine = GameEventEngine()
        event = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
        deltas = engine.process_event(event)
        
        # Find trust delta (positive emotion)
        trust_delta = next(d for d in deltas if d.emotion == "trust")
        assert trust_delta.scaled_by_intensity > 0
    
    def test_hostile_reduces_positive_emotions(self):
        """Hostile relationship should reduce positive emotion deltas."""
        engine = GameEventEngine()
        event = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
        
        # Without grudge
        deltas_normal = engine.process_event(event)
        # With hostile grudge
        deltas_hostile = engine.process_event(event, relationship_type="hostile")
        
        # Compare trust delta (positive emotion)
        trust_normal = next(d for d in deltas_normal if d.emotion == "trust")
        trust_hostile = next(d for d in deltas_hostile if d.emotion == "trust")
        
        # Hostile should reduce trust by 50% (grudge_factor=0.5)
        assert trust_hostile.scaled_by_intensity < trust_normal.scaled_by_intensity
        assert abs(trust_hostile.scaled_by_intensity - trust_normal.scaled_by_intensity * 0.5) < 0.01
    
    def test_hostile_reduces_joy(self):
        """Hostile relationship should reduce joy from PLAYER_HELPED."""
        engine = GameEventEngine()
        event = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
        
        deltas_normal = engine.process_event(event)
        deltas_hostile = engine.process_event(event, relationship_type="hostile")
        
        joy_normal = next(d for d in deltas_normal if d.emotion == "joy")
        joy_hostile = next(d for d in deltas_hostile if d.emotion == "joy")
        
        assert joy_hostile.scaled_by_intensity < joy_normal.scaled_by_intensity
    
    def test_negative_emotions_not_reduced(self):
        """Grudge factor should NOT reduce negative emotions."""
        engine = GameEventEngine()
        event = GameEvent(GameEventType.PLAYER_ATTACKED, intensity=1.0)
        
        deltas_normal = engine.process_event(event)
        deltas_hostile = engine.process_event(event, relationship_type="hostile")
        
        # Anger is a negative emotion, should not be reduced
        anger_normal = next(d for d in deltas_normal if d.emotion == "anger")
        anger_hostile = next(d for d in deltas_hostile if d.emotion == "anger")
        
        assert anger_hostile.scaled_by_intensity == anger_normal.scaled_by_intensity
    
    def test_enemy_grudge_greater_than_hostile(self):
        """Enemy relationship should have stronger grudge than hostile."""
        engine = GameEventEngine()
        event = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
        
        deltas_hostile = engine.process_event(event, relationship_type="hostile")
        deltas_enemy = engine.process_event(event, relationship_type="enemy")
        
        trust_hostile = next(d for d in deltas_hostile if d.emotion == "trust")
        trust_enemy = next(d for d in deltas_enemy if d.emotion == "trust")
        
        # Enemy (0.6) should reduce more than hostile (0.5)
        assert trust_enemy.scaled_by_intensity < trust_hostile.scaled_by_intensity
    
    def test_neutral_relationship_no_reduction(self):
        """Neutral relationship should not reduce positive emotions."""
        engine = GameEventEngine()
        event = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
        
        deltas_normal = engine.process_event(event)
        deltas_neutral = engine.process_event(event, relationship_type="neutral")
        
        trust_normal = next(d for d in deltas_normal if d.emotion == "trust")
        trust_neutral = next(d for d in deltas_neutral if d.emotion == "trust")
        
        assert trust_neutral.scaled_by_intensity == trust_normal.scaled_by_intensity
    
    def test_unknown_relationship_no_grudge(self):
        """Unknown relationship type should default to no grudge."""
        engine = GameEventEngine()
        event = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
        
        deltas_normal = engine.process_event(event)
        deltas_unknown = engine.process_event(event, relationship_type="some_random_type")
        
        trust_normal = next(d for d in deltas_normal if d.emotion == "trust")
        trust_unknown = next(d for d in deltas_unknown if d.emotion == "trust")
        
        assert trust_unknown.scaled_by_intensity == trust_normal.scaled_by_intensity
    
    def test_gift_given_reduced_by_grudge(self):
        """Gift giving should have reduced positive effect with hostile source."""
        engine = GameEventEngine()
        event = GameEvent(GameEventType.GIFT_GIVEN, intensity=1.0)
        
        deltas_normal = engine.process_event(event)
        deltas_hostile = engine.process_event(event, relationship_type="hostile")
        
        joy_normal = next(d for d in deltas_normal if d.emotion == "joy")
        joy_hostile = next(d for d in deltas_hostile if d.emotion == "joy")
        
        assert joy_hostile.scaled_by_intensity < joy_normal.scaled_by_intensity


class TestGrudgeFactorHighAgreeableness:
    """Tests specifically for the high-agreeableness NPC forgiveness issue."""
    
    def test_high_agreeableness_still_slow_to_forgive_hostile(self):
        """
        A high-agreeableness NPC with a hostile relationship should still
        not quickly forgive (positive events from hostile source are reduced).
        """
        high_agreeableness = {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.9,  # Very high
            "neuroticism": 0.3,
        }
        engine = GameEventEngine(personality=high_agreeableness)
        
        # Simulate: hostile player helps NPC
        event = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
        deltas = engine.process_event(event, relationship_type="hostile")
        
        # Trust should be reduced despite high agreeableness modifier
        trust_delta = next(d for d in deltas if d.emotion == "trust")
        
        # Without grudge, high agreeableness would amplify trust
        deltas_no_grudge = engine.process_event(event)
        trust_no_grudge = next(d for d in deltas_no_grudge if d.emotion == "trust")
        
        # With grudge, trust should be significantly less
        assert trust_delta.scaled_by_intensity < trust_no_grudge.scaled_by_intensity

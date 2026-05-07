"""
Neshama Emotion Fast Path Tests
"""

import pytest
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.soul.emotion.game_event import GameEvent, GameEventType
from neshama.soul.emotion.fast_path import (
    EmotionFastPath,
    FastPathResult,
    ResponseHint,
    ResponseTone,
    Urgency,
    SuggestedAction,
    create_fast_path,
)


class TestEmotionFastPathInit:
    """Tests for EmotionFastPath initialization."""

    def test_default_init(self):
        """Test default initialization."""
        fast_path = EmotionFastPath()
        assert fast_path._emotion_engine is not None
        assert fast_path._event_engine is not None
        assert fast_path.processing_count == 0

    def test_custom_neuroticism(self):
        """Test initialization with custom neuroticism."""
        fast_path = EmotionFastPath(neuroticism=0.8)
        assert fast_path._emotion_engine.neuroticism == 0.8

    def test_custom_personality(self):
        """Test initialization with personality."""
        personality = {
            "openness": 0.7,
            "extraversion": 0.8,
        }
        fast_path = EmotionFastPath(personality=personality)
        assert fast_path._event_engine.personality["extraversion"] == 0.8


class TestFastPathProcess:
    """Tests for FastPath.process()."""

    def test_process_single_event(self):
        """Test processing a single event."""
        fast_path = EmotionFastPath()
        event = GameEvent(GameEventType.PLAYER_HELPED, intensity=1.0)
        
        result = fast_path.process(event)
        
        assert isinstance(result, FastPathResult)
        assert "trust" in result.emotion_state
        assert "joy" in result.emotion_state
        assert result.processing_time_ms >= 0

    def test_process_updates_emotion_state(self):
        """Test that processing updates internal emotion state."""
        fast_path = EmotionFastPath()
        event = GameEvent(GameEventType.QUEST_COMPLETED, intensity=1.0)
        
        result = fast_path.process(event)
        
        # Internal state should be updated
        state = fast_path.get_current_state()
        assert "joy" in state["emotion_state"]
        assert state["emotion_state"]["joy"] > 0

    def test_process_increments_count(self):
        """Test that processing increments the counter."""
        fast_path = EmotionFastPath()
        assert fast_path.processing_count == 0
        
        fast_path.process(GameEvent(GameEventType.PLAYER_HELPED))
        assert fast_path.processing_count == 1
        
        fast_path.process(GameEvent(GameEventType.QUEST_COMPLETED))
        assert fast_path.processing_count == 2

    def test_process_returns_composite(self):
        """Test that composite emotion is returned."""
        fast_path = EmotionFastPath()
        
        # Joy + Trust → Love
        fast_path.process(GameEvent(GameEventType.GIFT_GIVEN, intensity=1.0))
        
        state = fast_path.get_current_state()
        assert state["composite_emotion"] is not None


class TestResponseHints:
    """Tests for response hint generation."""

    def test_joy_generates_friendly_hint(self):
        """Test that joy generates friendly response hints."""
        fast_path = EmotionFastPath()
        # With BUG fix (adjust_emotion uses 0+delta instead of 0.5+delta),
        # QUEST_COMPLETED gives joy=0.4 which is below the 0.5 JOYFUL threshold,
        # resulting in NEUTRAL tone. Use high-intensity repeated events to reach JOYFUL.
        event = GameEvent(GameEventType.QUEST_COMPLETED, intensity=1.0)
        result = fast_path.process(event)
        
        # After fix, first event gives joy=0.4 → NEUTRAL. Process again to accumulate.
        result2 = fast_path.process(event)
        
        # With accumulated joy > 0.5, tone should be JOYFUL
        assert result2.response_hint.tone in [
            ResponseTone.JOYFUL,
            ResponseTone.FRIENDLY,
            ResponseTone.PROUD,
        ]

    def test_anger_generates_hostile_hint(self):
        """Test that high anger generates hostile hints."""
        fast_path = EmotionFastPath()
        
        # Generate anger
        for _ in range(3):
            fast_path.process(GameEvent(GameEventType.NPC_INSULTED, intensity=1.0))
        
        result = fast_path.get_current_state()
        hint = fast_path._generate_hint(
            result["emotion_state"],
            None
        )
        
        assert hint.tone == ResponseTone.HOSTILE
        assert SuggestedAction.DIALOGUE_HOSTILE in hint.suggested_actions

    def test_fear_generates_nervous_hint(self):
        """Test that fear generates nervous/cautious hints."""
        fast_path = EmotionFastPath()
        
        # Generate fear with only fear events
        fast_path.clear()
        for _ in range(2):
            fast_path.process(GameEvent(GameEventType.DEATH_WITNESSED, intensity=1.0))
        
        result = fast_path.get_current_state()
        hint = fast_path._generate_hint(
            result["emotion_state"],
            None
        )
        
        # Fear or high surprise should dominate
        assert hint.tone in [ResponseTone.FEARFUL, ResponseTone.NERVOUS, ResponseTone.SURPRISED, ResponseTone.SAD]

    def test_trust_generates_trusting_hint(self):
        """Test that trust generates trusting hints."""
        fast_path = EmotionFastPath()
        fast_path.clear()
        
        # Generate trust without joy - use relationship_changed
        for _ in range(2):
            fast_path.process(GameEvent(GameEventType.RELATIONSHIP_CHANGED, intensity=1.0))
        
        result = fast_path.get_current_state()
        hint = fast_path._generate_hint(
            result["emotion_state"],
            None
        )
        
        # Trust should be present, may be joyful or trusting depending on composition
        assert hint.tone in [ResponseTone.TRUSTING, ResponseTone.JOYFUL, ResponseTone.FRIENDLY]

    def test_hint_has_confidence(self):
        """Test that hints have confidence scores."""
        fast_path = EmotionFastPath()
        event = GameEvent(GameEventType.QUEST_COMPLETED, intensity=1.0)
        
        result = fast_path.process(event)
        
        assert 0 <= result.response_hint.confidence <= 1

    def test_hint_includes_reasoning(self):
        """Test that hints include reasoning."""
        fast_path = EmotionFastPath()
        event = GameEvent(GameEventType.QUEST_COMPLETED, intensity=1.0)
        
        result = fast_path.process(event)
        
        assert len(result.response_hint.reasoning) > 0

    def test_urgency_based_on_emotion_intensity(self):
        """Test that urgency increases with emotion intensity."""
        fast_path = EmotionFastPath()
        
        # Low intensity
        event_low = GameEvent(GameEventType.NPC_INSULTED, intensity=0.3)
        result_low = fast_path.process(event_low)
        
        # High intensity
        event_high = GameEvent(GameEventType.NPC_INSULTED, intensity=1.0)
        result_high = fast_path.process(event_high)
        
        # Higher intensity should give higher or equal urgency
        urgency_order = {Urgency.LOW: 0, Urgency.MEDIUM: 1, Urgency.HIGH: 2}
        assert urgency_order[result_high.response_hint.urgency] >= urgency_order[result_low.response_hint.urgency]


class TestFastPathPerformance:
    """Tests for fast path performance requirements."""

    def test_single_process_under_10ms(self):
        """Test that single event processing is under 10ms."""
        fast_path = EmotionFastPath()
        event = GameEvent(GameEventType.PLAYER_HELPED, intensity=0.8)
        
        # Warm up
        fast_path.process(event)
        
        # Measure
        times = []
        for _ in range(10):
            start = time.perf_counter()
            fast_path.process(GameEvent(GameEventType.QUEST_COMPLETED, intensity=0.8))
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Average should be well under 10ms
        assert avg_time < 10, f"Average time {avg_time:.2f}ms exceeds 10ms"
        assert max_time < 20, f"Max time {max_time:.2f}ms is too high"

    def test_result_includes_processing_time(self):
        """Test that result includes processing time."""
        fast_path = EmotionFastPath()
        event = GameEvent(GameEventType.PLAYER_HELPED)
        
        result = fast_path.process(event)
        
        assert result.processing_time_ms >= 0
        assert result.processing_time_ms < 100  # Should be reasonable


class TestFastPathState:
    """Tests for fast path state management."""

    def test_clear_emotions(self):
        """Test clearing all emotions."""
        fast_path = EmotionFastPath()
        
        # Add emotions
        fast_path.process(GameEvent(GameEventType.QUEST_COMPLETED, intensity=1.0))
        
        # Clear
        fast_path.clear()
        
        state = fast_path.get_current_state()
        assert len(state["emotion_state"]) == 0

    def test_tick_decay(self):
        """Test time-based emotion decay."""
        fast_path = EmotionFastPath()
        
        # Add emotions
        fast_path.process(GameEvent(GameEventType.QUEST_COMPLETED, intensity=1.0))
        
        state_before = fast_path.get_current_state()
        joy_before = state_before["emotion_state"].get("joy", 0)
        
        # Tick with time
        fast_path.tick(delta_seconds=120.0)  # 2 minutes
        
        state_after = fast_path.get_current_state()
        joy_after = state_after["emotion_state"].get("joy", 0)
        
        # Joy should have decayed
        assert joy_after < joy_before

    def test_get_current_state(self):
        """Test getting current state."""
        fast_path = EmotionFastPath()
        
        # Initially empty
        state = fast_path.get_current_state()
        assert "emotion_state" in state
        assert "composite_emotion" in state


class TestFastPathResult:
    """Tests for FastPathResult.to_dict()."""

    def test_to_dict_unity_friendly(self):
        """Test that to_dict is Unity-friendly (flat)."""
        fast_path = EmotionFastPath()
        event = GameEvent(GameEventType.PLAYER_HELPED, intensity=0.8)
        
        result = fast_path.process(event)
        result_dict = result.to_dict()
        
        # Check top-level keys (no deep nesting for main fields)
        assert "emotion_state" in result_dict
        assert "composite_emotion" in result_dict
        assert "response_hint" in result_dict
        assert "processing_time_ms" in result_dict
        
        # Check response_hint is flat
        hint = result_dict["response_hint"]
        assert "tone" in hint
        assert "urgency" in hint
        assert "suggested_actions" in hint


class TestFactoryFunction:
    """Tests for factory function."""

    def test_create_fast_path(self):
        """Test factory function creates fast path."""
        fast_path = create_fast_path()
        assert isinstance(fast_path, EmotionFastPath)

    def test_create_with_params(self):
        """Test factory with parameters."""
        fast_path = create_fast_path(neuroticism=0.3, personality={"extraversion": 0.9})
        assert fast_path._emotion_engine.neuroticism == 0.3
        assert fast_path._event_engine.personality["extraversion"] == 0.9

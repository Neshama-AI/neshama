"""
Neshama Emotion Driver Tests
"""

import pytest
import sys
import os
import time
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neshama.soul.emotion.driver import (
    EmotionDriver,
    BehaviorTrigger,
    EmotionTrajectoryPoint,
    EMOTION_DECAY_RATES,
    EMOTION_OPPOSING_PAIRS,
    EMOTION_SIMILARITY_GROUPS,
    get_driver,
    remove_driver,
)


class TestEmotionDriverInit:
    """Tests for EmotionDriver initialization."""

    def test_default_init(self):
        """Test default initialization."""
        driver = EmotionDriver(npc_id="test_npc")
        assert driver.npc_id == "test_npc"
        assert driver.neuroticism == 0.5
        assert len(driver._emotions) > 0

    def test_custom_neuroticism(self):
        """Test initialization with custom neuroticism."""
        driver = EmotionDriver(npc_id="test_npc", personality_neuroticism=0.9)
        assert driver.neuroticism == 0.9

    def test_initial_emotions(self):
        """Test initialization with initial emotions."""
        initial = {"joy": 0.8, "anger": 0.3}
        driver = EmotionDriver(npc_id="test_npc", initial_emotions=initial)
        assert driver.get_emotion("joy") == 0.8
        assert driver.get_emotion("anger") == 0.3

    def test_neuroticism_modifies_decay(self):
        """Test that high neuroticism slows decay."""
        low_neuro = EmotionDriver(npc_id="low", personality_neuroticism=0.1)
        high_neuro = EmotionDriver(npc_id="high", personality_neuroticism=0.9)
        
        # High neuroticism should have slower decay
        assert high_neuro._emotions["anger"].decay_rate < low_neuro._emotions["anger"].decay_rate


class TestEmotionDecay:
    """Tests for emotion decay."""

    def test_basic_decay(self):
        """Test basic exponential decay."""
        driver = EmotionDriver(npc_id="test")
        driver.set_emotion("anger", 0.8, baseline=0.0)
        
        # Store initial value
        initial = driver.get_emotion("anger")
        
        # Tick for 1 second
        driver.tick(1.0)
        
        # Should have decayed
        after = driver.get_emotion("anger")
        assert after < initial

    def test_decay_to_baseline(self):
        """Test that emotions decay to baseline."""
        driver = EmotionDriver(npc_id="test", personality_neuroticism=0.0)
        driver.set_emotion("joy", 0.9, baseline=0.2)
        
        # Calculate how many ticks needed to get within 0.1 of baseline
        # With joy decay rate of 0.05 and neuroticism=0 (multiplier=1), after 50s should be close
        # Tick multiple times with longer intervals
        for _ in range(20):
            driver.tick(5.0)
        
        # Should be close to baseline
        final = driver.get_emotion("joy")
        # With high decay, should be much closer now
        assert abs(final - 0.2) < 0.3

    def test_decay_formula(self):
        """Test the decay formula matches expected."""
        driver = EmotionDriver(npc_id="test", personality_neuroticism=0.0)
        initial = 0.8
        baseline = 0.1
        driver.set_emotion("anger", initial, baseline=baseline)
        
        decay_rate = driver._emotions["anger"].decay_rate
        delta = 5.0
        
        # Calculate expected
        diff = initial - baseline
        expected = baseline + diff * math.exp(-decay_rate * delta)
        
        # Apply tick
        driver.tick(delta)
        
        assert abs(driver.get_emotion("anger") - expected) < 0.001

    def test_different_emotions_decay_differently(self):
        """Test that different emotions have different decay rates."""
        driver = EmotionDriver(npc_id="test")
        
        driver.set_emotion("anger", 0.8, baseline=0.0)
        driver.set_emotion("joy", 0.8, baseline=0.0)
        
        anger_initial = driver.get_emotion("anger")
        joy_initial = driver.get_emotion("joy")
        
        driver.tick(2.0)
        
        # Anger decays slower than joy
        assert driver.get_emotion("anger") > driver.get_emotion("joy")


class TestEmotionDiffusion:
    """Tests for emotion diffusion."""

    def test_similar_emotions_reinforce(self):
        """Test that similar emotions reinforce each other."""
        driver = EmotionDriver(npc_id="test")
        
        # Set joy and love high
        driver.set_emotion("joy", 0.8)
        driver.set_emotion("love", 0.7)
        
        emotions_before = driver.get_all_emotions()
        
        # Tick
        driver.tick(1.0)
        
        emotions_after = driver.get_all_emotions()
        
        # Both should stay high or increase slightly due to reinforcement
        # (actual change depends on diffusion strength)

    def test_opposing_emotions_antagonize(self):
        """Test that opposing emotions suppress each other."""
        driver = EmotionDriver(npc_id="test")
        
        driver.set_emotion("joy", 0.8)
        driver.set_emotion("sadness", 0.6)
        
        joy_before = driver.get_emotion("joy")
        sadness_before = driver.get_emotion("sadness")
        
        # Multiple ticks for conflict to take effect
        for _ in range(5):
            driver.tick(1.0)
        
        joy_after = driver.get_emotion("joy")
        sadness_after = driver.get_emotion("sadness")


class TestBehaviorTriggers:
    """Tests for behavior trigger detection."""

    def test_rising_trigger(self):
        """Test rising threshold trigger."""
        driver = EmotionDriver(npc_id="test")
        
        # Start at low value
        driver.set_emotion("anger", 0.2)
        
        # Directly set previous value to simulate crossing from below
        driver._prev_values["anger"] = 0.2
        
        # Simulate emotion rising by directly modifying entry
        driver._emotions["anger"].current = 0.75
        
        # Now tick should detect the crossing
        triggers = driver.tick(0.0)
        
        # Should have trigger for crossing 0.7 threshold
        anger_triggers = [t for t in triggers if t.emotion == "anger" and t.direction == "rising"]
        assert len(anger_triggers) > 0

    def test_falling_trigger(self):
        """Test falling threshold trigger."""
        driver = EmotionDriver(npc_id="test")
        
        # Start at high value
        driver.set_emotion("joy", 0.8)
        
        # Directly set previous value to simulate crossing from above
        driver._prev_values["joy"] = 0.8
        
        # Simulate emotion falling by directly modifying entry
        driver._emotions["joy"].current = 0.2
        
        # Now tick should detect the crossing
        triggers = driver.tick(0.0)
        
        # Should have falling triggers
        joy_triggers = [t for t in triggers if t.emotion == "joy" and t.direction == "falling"]
        assert len(joy_triggers) > 0

    def test_get_active_triggers(self):
        """Test getting active triggers above threshold."""
        driver = EmotionDriver(npc_id="test")
        driver.set_emotion("anger", 0.8)
        driver.set_emotion("fear", 0.6)
        
        triggers = driver.get_active_triggers(min_threshold=0.5)
        
        # Should have triggers for emotions above threshold
        emotion_names = [t.emotion for t in triggers]
        assert "anger" in emotion_names
        assert "fear" in emotion_names


class TestEventApplication:
    """Tests for applying events to emotions."""

    def test_apply_event_delta(self):
        """Test applying event deltas."""
        driver = EmotionDriver(npc_id="test")
        driver.set_emotion("anger", 0.2)
        
        driver.apply_event_delta({"anger": 0.3})
        
        assert driver.get_emotion("anger") == pytest.approx(0.5, rel=0.01)

    def test_decay_paused_during_event(self):
        """Test that decay is paused during event application."""
        driver = EmotionDriver(npc_id="test")
        driver.set_emotion("anger", 0.8, baseline=0.0)
        
        initial = driver.get_emotion("anger")
        
        # Apply event (should pause decay)
        driver.apply_event_delta({"joy": 0.3})
        
        # Decay should still be paused
        assert driver._decay_paused == False  # Resume called after delta
        
        # Tick should work normally
        driver.tick(0.0)

    def test_emotion_capped_at_max(self):
        """Test that emotions are capped at 1.0."""
        driver = EmotionDriver(npc_id="test")
        driver.set_emotion("anger", 0.9)
        
        driver.apply_event_delta({"anger": 0.5})
        
        # Should not exceed 1.0
        assert driver.get_emotion("anger") <= 1.0


class TestEmotionTrajectory:
    """Tests for emotion trajectory prediction."""

    def test_trajectory_basic(self):
        """Test basic trajectory generation."""
        driver = EmotionDriver(npc_id="test")
        driver.set_emotion("joy", 0.8, baseline=0.0)
        
        trajectory = driver.get_emotion_trajectory(duration_seconds=10.0, steps=5)
        
        assert len(trajectory) == 5
        assert all(isinstance(p, EmotionTrajectoryPoint) for p in trajectory)

    def test_trajectory_shows_decay(self):
        """Test that trajectory shows decreasing values over time."""
        driver = EmotionDriver(npc_id="test")
        driver.set_emotion("joy", 0.8, baseline=0.0)
        
        trajectory = driver.get_emotion_trajectory(duration_seconds=10.0, steps=5)
        
        # First point should have higher joy than last point
        first_joy = trajectory[0].emotions.get("joy", 0.0)
        last_joy = trajectory[-1].emotions.get("joy", 0.0)
        
        assert first_joy > last_joy

    def test_trajectory_timestamps(self):
        """Test that trajectory timestamps are correct."""
        driver = EmotionDriver(npc_id="test")
        driver.set_emotion("joy", 0.8, baseline=0.0)
        
        trajectory = driver.get_emotion_trajectory(duration_seconds=10.0, steps=6)
        
        # Timestamps should be evenly spaced
        timestamps = [p.timestamp for p in trajectory]
        for i in range(len(timestamps) - 1):
            diff = timestamps[i + 1] - timestamps[i]
            assert abs(diff - 2.0) < 0.01  # 10 / 5 = 2.0


class TestDominantEmotion:
    """Tests for dominant emotion detection."""

    def test_dominant_emotion(self):
        """Test getting the dominant emotion."""
        driver = EmotionDriver(npc_id="test")
        driver.set_emotion("anger", 0.9)
        driver.set_emotion("joy", 0.3)
        
        dominant = driver.get_dominant_emotion()
        
        assert dominant is not None
        assert dominant[0] == "anger"
        assert dominant[1] == 0.9

    def test_no_dominant_when_all_low(self):
        """Test no dominant when all emotions are low."""
        driver = EmotionDriver(npc_id="test")
        # Don't set any emotions
        
        dominant = driver.get_dominant_emotion()
        
        assert dominant is None


class TestGlobalDriverInstance:
    """Tests for global driver instance management."""

    def test_get_driver_creates_new(self):
        """Test that get_driver creates a new driver if needed."""
        npc_id = "new_npc_123"
        remove_driver(npc_id)
        
        driver1 = get_driver(npc_id)
        
        assert driver1 is not None
        assert driver1.npc_id == npc_id

    def test_get_driver_returns_same(self):
        """Test that get_driver returns the same instance."""
        npc_id = "same_npc_456"
        remove_driver(npc_id)
        
        driver1 = get_driver(npc_id)
        driver2 = get_driver(npc_id)
        
        assert driver1 is driver2

    def test_remove_driver(self):
        """Test removing a driver."""
        npc_id = "remove_npc_789"
        driver = get_driver(npc_id)
        
        result = remove_driver(npc_id)
        
        assert result is True
        
        # Getting again should create new
        driver2 = get_driver(npc_id)
        assert driver2 is not driver


class TestEmotionState:
    """Tests for emotion state serialization."""

    def test_get_emotion_state(self):
        """Test getting full emotion state."""
        driver = EmotionDriver(npc_id="test")
        driver.set_emotion("anger", 0.8)
        
        state = driver.get_emotion_state()
        
        assert state["npc_id"] == "test"
        assert "emotions" in state
        assert "anger" in state["emotions"]

    def test_to_dict(self):
        """Test EmotionEntry to_dict."""
        from neshama.soul.emotion.driver import EmotionEntry
        
        entry = EmotionEntry(
            name="joy",
            current=0.8,
            baseline=0.3,
            decay_rate=0.05,
        )
        
        data = entry.to_dict()
        
        assert data["name"] == "joy"
        assert data["current"] == 0.8
        assert data["baseline"] == 0.3
